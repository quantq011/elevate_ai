# chromastore.py
from typing import Optional, Dict, List, Callable
import json
try:
    import chromadb
    # from chromadb.config import Settings
except Exception:
    chromadb = None

# try:
#     from openai import OpenAI
# except Exception:
#     OpenAI = None

def _sanitize_meta(m):
    clean = {}
    for k, v in (m or {}).items():
        if k == "embedding":
            # handled separately; do not keep it in metadata
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            clean[k] = v
        else:
            # stringify non-primitives (lists/dicts/objects)
            try:
                clean[k] = json.dumps(v, ensure_ascii=False)
            except Exception:
                clean[k] = str(v)
    return clean

# class AzureOpenAIEmbeddingFunction:
#     """Chroma-compatible embedder for Azure OpenAI (deployment name required)."""
#     def __init__(self, openai_client, deployment: Optional[str] = None):
#         if openai_client is None:
#             raise ValueError("openai_client is required")
#         self.client = openai_client
#         # MUST be your Azure *deployment name*, not a base model id.
#         self.model = deployment or os.getenv("EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
#         self.name = f"azure-openai:{self.model}"

#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         if not texts:
#             return []
#         resp = self.client.embeddings.create(model=self.model, input=texts)
#         return [d.embedding for d in resp.data]

#     def embed_query(self, text: str) -> List[float]:
#         resp = self.client.embeddings.create(model=self.model, input=[text])
#         return resp.data[0].embedding

#     # --- Chroma entrypoint (newer interface) ---
#     def __call__(self, input: List[str] = None, **kwargs) -> List[List[float]]:
#         """
#         Chroma >=0.4.16 calls the embedding function like: ef(input=[...]).
#         We also accept older kw 'texts' if Chroma provides it.
#         """
#         if input is None:
#             input = kwargs.pop("texts", None)  # backward-compat
#         if not input:
#             return []
#         resp = self.client.embeddings.create(model=self.model, input=input)
#         return [d.embedding for d in resp.data]

#     # --- Convenience methods some tooling checks for ---
#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         if not texts:
#             return []
#         resp = self.client.embeddings.create(model=self.model, input=texts)
#         return [d.embedding for d in resp.data]

#     def embed_query(self, text: str) -> List[float]:
#         resp = self.client.embeddings.create(model=self.model, input=[text])
#         return resp.data[0].embedding

class ChromaStore:
    def __init__(self, collection_name: str = "knowledge", openai_client: Optional[object] = None):
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
        try:
            self.client = chromadb.Client()
        except Exception:
            self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=None))

        self.collection_name = collection_name
        print("ChromaStore init, collection:", collection_name)
        # self.emb_fn = None
        # if openai_client is not None:
        #     deployment = os.getenv("EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        #     self.emb_fn = OpenAIEmbeddingFunction(openai_client, deployment=deployment)
        # # ✅ defensive check: embedding_function must NOT be a string
        # if isinstance(self.emb_fn, (str, bytes)):
        #     raise TypeError("embedding_function cannot be a string; pass an object with __call__/embed_* methods.")
        # Create or get collection
        if hasattr(self.client, "get_or_create_collection"):
            # try:
            #     self.collection = self.client.get_or_create_collection(
            #         name=self.collection_name,
            #         embedding_function=self.emb_fn  # <-- the OBJECT
            #     )
            # except Exception as e:
            #     print("ChromaStore init, exception caught:", e)
            try:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=OpenAIEmbeddingFunction(
                        model_name="text-embedding-3-small"
                    )
                )
            except Exception as e:
                print("ChromaStore init, exception caught:", e)
        else:
            try:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=OpenAIEmbeddingFunction(
                        model_name="text-embedding-3-small"
                    )
                )
            except Exception as e:
                self.collection = self.client.get_collection(name=self.collection_name)
                print("ChromaStore init, exception caught:", e)

    def upsert_documents(self, docs: List[Dict]):
        ids = [d["id"] for d in docs]
        texts = [d.get("text", "") for d in docs]
        raw_metas = [d.get("metadata", {}) for d in docs]

        coll_has_emb = getattr(self.collection, "embedding_function", None) is not None

        if not coll_has_emb:
            # Expect precomputed embeddings; pop them out of metadata
            embeddings = []
            clean_metas = []
            for m in raw_metas:
                e = (m or {}).pop("embedding", None)
                if e is None:
                    raise ValueError(
                        "Collection has no embedding function; provide an 'embedding' vector per doc"
                    )
                embeddings.append(e)
                clean_metas.append(_sanitize_meta(m))
            self.collection.add(ids=ids, embeddings=embeddings, metadatas=clean_metas, documents=texts)
        else:
            # Collection embeds internally; just sanitize metadata
            clean_metas = [_sanitize_meta(m) for m in raw_metas]
            self.collection.add(ids=ids, documents=texts, metadatas=clean_metas)

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: Optional[Dict] = None,
        embedder: Optional[Callable[[List[str]], List[List[float]]]] = None
    ):
        if getattr(self.collection, "embedding_function", None) is None:
            # No collection embedder → need a query vector
            if embedder is None:
                raise RuntimeError("Collection has no embedding function; pass embedder=... to query()")
            qvec = embedder([query_text])[0]
            res = self.collection.query(query_embeddings=[qvec], n_results=top_k, where=where)
        else:
            # Normal path: Chroma embeds internally
            res = self.collection.query(query_texts=[query_text], n_results=top_k, where=where)

        results = []
        if res:
            for ids, docs, scores, metadatas in zip(
                res.get("ids", []), res.get("documents", []), res.get("distances", []), res.get("metadatas", [])
            ):
                for i, _id in enumerate(ids):
                    results.append({
                        "id": _id,
                        "document": (docs[i] if docs else None),
                        "score": (scores[i] if scores else None),
                        "metadata": (metadatas[i] if metadatas else None),
                    })
        return results


class FallbackChromaStore:
    """Naive in-memory fallback with optional 'where' filtering."""
    def __init__(self, collection_name: str = "knowledge", openai_client: Optional[object] = None):
        self.docs = {}  # id -> (text, metadata)

    def upsert_documents(self, docs: List[Dict]):
        for d in docs:
            _id = d.get("id")
            if not _id:
                raise ValueError("each doc needs an 'id'")
            self.docs[_id] = (d.get("text", ""), d.get("metadata", {}))

    def query(self, query_text: str, top_k: int = 5, where: Optional[Dict] = None):
        if not query_text:
            return []

        def meta_match(meta: Dict, where: Optional[Dict]) -> bool:
            if not where:
                return True
            for k, v in where.items():
                if meta.get(k) != v:
                    return False
            return True

        qtokens = [t for t in query_text.lower().split() if t]
        scored = []
        for _id, (text, meta) in self.docs.items():
            if not meta_match(meta, where):
                continue
            tokens = [t for t in text.lower().split() if t]
            score = sum(tokens.count(t) for t in qtokens)
            if score > 0:
                snippet = text if len(text) <= 260 else text[:260] + "..."
                scored.append((score, _id, snippet, meta))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"id": _id, "document": doc, "score": sc, "metadata": meta} for sc, _id, doc, meta in scored[:top_k]]


def create_store(collection_name: str = "knowledge", openai_client: Optional[object] = None):
    if chromadb is None:
        print("chromadb not installed; using FallbackChromaStore")
        return FallbackChromaStore(collection_name=collection_name, openai_client=openai_client)
    try:
        return ChromaStore(collection_name=collection_name, openai_client=openai_client)
    except Exception as e:
        print("ChromaStore initialization failed; falling back. Error:", e)
        return FallbackChromaStore(collection_name=collection_name, openai_client=openai_client)