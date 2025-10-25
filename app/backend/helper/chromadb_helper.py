import time
import hashlib
from typing import List, Dict, Optional, Callable
from typing import Optional
from backend.chromastore import ChromaStore

#load_dotenv()
#AZURE_API_KEY  = os.getenv("AZURE_OPENAI_API_KEY")
#AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

#client = OpenAI(api_key=AZURE_API_KEY, base_url=AZURE_ENDPOINT)
#STORE = create_store(openai_client=client)  # uses text-embedding-3-small internally:contentReference[oaicite:2]{index=2}
def log_turn_to_chroma(
    store,
    text: str,
    session_id: Optional[str],
    role: str,                               # "user" | "assistant" | etc.
    extra_meta: Optional[Dict] = None,
    *,
    # Only needed if your Chroma collection was created WITHOUT an embedding function:
    # embedder must be: Callable[[List[str]], List[List[float]]]
    embedder: Optional[Callable[[List[str]], List[List[float]]]] = None,
    # Simple char-based chunking (safe default for chat logs)
    max_chunk_chars: int = 1500,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Logs a chat turn (possibly chunked) into Chroma via your store.

    If the underlying Chroma collection has an embedding function attached,
    embeddings are computed automatically inside Chroma.

    If NOT, you must pass `embedder`, and we will precompute embeddings and
    attach them in metadata for each chunk (as your store expects).
    """
    if not text or not text.strip():
        return []

    now_ms = int(time.time() * 1000)
    sid = session_id or "anon"

    # ---- Chunk (simple char-based; good enough for chat) ----
    t = text.strip()
    chunks: List[str] = []
    if len(t) <= max_chunk_chars:
        chunks = [t]
    else:
        step = max(1, max_chunk_chars - max(0, chunk_overlap))
        for i in range(0, len(t), step):
            chunk = t[i:i + max_chunk_chars]
            if chunk:
                chunks.append(chunk)

    n = len(chunks)
    # Stable-ish hash of the text content to help detect accidental duplicates
    content_hash = hashlib.blake2b(t.encode("utf-8"), digest_size=8).hexdigest()

    # ---- Prepare docs ----
    base_meta = {
        "session_id": sid,
        "role": role,
        "ts_ms": now_ms,
        "kind": "chat",
        "content_hash": content_hash,
    }
    if extra_meta:
        base_meta.update(extra_meta)

    ids: List[str] = []
    docs: List[Dict] = []

    # If the collection has NO embedding function, we may need to compute embeddings here
    coll_has_emb = bool(getattr(getattr(store, "collection", None), "embedding_function", None))

    # Precompute embeddings if required
    precomputed_embs: Optional[List[List[float]]] = None
    if not coll_has_emb:
        if embedder is None:
            raise RuntimeError(
                "Chroma collection has no embedding function. "
                "Pass embedder=Callable[[List[str]], List[List[float]]] to log_turn_to_chroma(), "
                "or recreate the collection with an embedding function attached."
            )
        precomputed_embs = embedder(chunks) if chunks else []

    for i, chunk in enumerate(chunks):
        doc_id = f"{sid}:{now_ms}:{role}:c{i+1}of{n}"
        ids.append(doc_id)
        meta = dict(base_meta)
        meta.update({"chunk_idx": i + 1, "chunk_total": n})

        entry = {
            "id": doc_id,
            "text": chunk,
            "metadata": meta,
        }

        # Attach per-chunk embedding only when the collection has no embedding function
        if not coll_has_emb and precomputed_embs is not None:
            # Your store expects embeddings inside metadata for add() in this mode
            meta["embedding"] = precomputed_embs[i]

        docs.append(entry)

    # ---- Upsert ----
    store.upsert_documents(docs)
    return ids


def retrieve_kb(store, query_text: str, k: int = 3, embedder: Optional[Callable[[List[str]], List[List[float]]]] = None):
    where = {"kind": {"$eq": "kb"}}
    return store.query(query_text, top_k=k, where=where, embedder=embedder)

def retrieve_session_mem(store, query_text: str, session_id: Optional[str], k: int = 3, embedder: Optional[Callable[[List[str]], List[List[float]]]] = None):
    sid = session_id or "anon"
    where = {"$and": [
        {"kind": {"$eq": "chat"}},
        {"session_id": {"$eq": sid}},
    ]}
    return store.query(query_text, top_k=k, where=where, embedder=embedder)

def to_bullets(results):
    out = []
    for r in results:
        src = r.get("metadata", {}).get("source", "kb")
        out.append(f"- ({src}) {r['document']}")
    return "\n".join(out)