# backend/docstore.py
import os, re, glob
from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass
class DocChunk:
    doc_id: int
    path: str
    title: str
    text: str

class DocStore:
    """
    Nạp .md dưới documents/, tách chunk theo tiêu đề/đoạn.
    Search: điểm số = tổng số lần khớp từ khóa (rất nhẹ, không phụ thuộc thư viện).
    """
    def __init__(self, root: str = "documents", max_chunk_len: int = 800):
        self.root = root
        self.max_chunk_len = max_chunk_len
        self.chunks: List[DocChunk] = []
        self._load()

    def _split_markdown(self, content: str) -> List[Tuple[str, str]]:
        # Tách theo heading #, ##, ### ...; nếu không có heading, gom theo đoạn.
        parts: List[Tuple[str, str]] = []
        sections = re.split(r"(?m)^#{1,6}\s+", content)
        heads = re.findall(r"(?m)^#{1,6}\s+(.+)$", content)
        if not sections or len(sections) == 1:
            # không có heading → cắt theo độ dài
            text = content.strip()
            for i in range(0, len(text), self.max_chunk_len):
                parts.append(("(no heading)", text[i:i+self.max_chunk_len]))
            return parts
        # phần đầu trước heading đầu tiên (nếu có)
        before = sections[0].strip()
        if before:
            parts.append(("(intro)", before[: self.max_chunk_len]))
        # các section có heading
        for h, body in zip(heads, sections[1:]):
            body = body.strip()
            if not body:
                parts.append((h.strip(), "")); continue
            # cắt body theo max_chunk_len
            for i in range(0, len(body), self.max_chunk_len):
                parts.append((h.strip(), body[i:i+self.max_chunk_len]))
        return parts

    def _load(self):
        doc_id = 0
        for path in glob.glob(os.path.join(self.root, "**", "*.md"), recursive=True):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                for (title, text) in self._split_markdown(content):
                    self.chunks.append(DocChunk(doc_id=doc_id, path=path, title=title, text=text))
                    doc_id += 1
            except Exception as e:
                print(f"[DocStore] Skip {path}: {e}")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if not query.strip():
            return []
        tokens = [t for t in re.split(r"\W+", query.lower()) if t]
        scored: List[Tuple[int, int]] = []  # (idx, score)
        for idx, ch in enumerate(self.chunks):
            text = ch.text.lower()
            score = sum(text.count(t) for t in tokens)
            if score > 0:
                scored.append((idx, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        hits = []
        for idx, score in scored[:top_k]:
            ch = self.chunks[idx]
            # lấy snippet ngắn
            snippet = ch.text.strip().replace("\n", " ")
            if len(snippet) > 260:
                snippet = snippet[:260] + "..."
            hits.append({
                "path": ch.path,
                "title": ch.title,
                "score": score,
                "snippet": snippet
            })
        return hits
