import logging
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import fitz
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import (
    ALLOWED_EXTENSIONS,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBED_MODEL,
    FAISS_INDEX_PATH,
    UPLOAD_DIR,
)
from .storage import (
    all_chunks_with_embeddings,
    chunk_by_id,
    chunk_id_by_row,
    create_document,
    delete_document,
    insert_chunks,
    set_faiss_mapping,
)

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self) -> None:
        self.embedder = SentenceTransformer(EMBED_MODEL)
        self.dim = self.embedder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dim)
        self.load_or_rebuild_index()

    def sanitize_filename(self, filename: str) -> str:
        safe = Path(filename).name
        safe = re.sub(r"[^a-zA-Z0-9._-]", "_", safe)
        return safe

    def validate_extension(self, filename: str) -> None:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("Unsupported file type. Allowed: .pdf, .txt, .md")

    def extract_text(self, filepath: Path) -> List[Tuple[Optional[int], str]]:
        ext = filepath.suffix.lower()
        if ext == ".pdf":
            doc = fitz.open(filepath)
            pages = []
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if text:
                    pages.append((i, text))
            doc.close()
            return pages
        text = filepath.read_text(encoding="utf-8", errors="ignore").strip()
        return [(None, text)] if text else []

    def chunk_text(self, text: str) -> List[str]:
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = min(len(text), start + CHUNK_SIZE)
            chunks.append(text[start:end])
            if end == len(text):
                break
            start = max(end - CHUNK_OVERLAP, start + 1)
        return chunks

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        vectors = self.embedder.encode(texts, convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(vectors)
        return vectors

    def upload_document(self, filename: str, content: bytes) -> Dict:
        safe_name = self.sanitize_filename(filename)
        self.validate_extension(safe_name)

        save_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{safe_name}"
        save_path.write_bytes(content)
        doc_id = create_document(safe_name, save_path)

        pages = self.extract_text(save_path)
        chunk_rows = []
        chunk_texts = []
        for page_num, text in pages:
            for idx, chunk in enumerate(self.chunk_text(text)):
                chunk_id = f"d{doc_id}_p{page_num or 0}_c{idx}_{uuid.uuid4().hex[:8]}"
                chunk_rows.append((chunk_id, doc_id, page_num, chunk))
                chunk_texts.append(chunk)

        if chunk_rows:
            vectors = self.embed_texts(chunk_texts)
            payload = []
            for row, vec in zip(chunk_rows, vectors):
                chunk_id, d_id, p_num, c_text = row
                payload.append((chunk_id, d_id, p_num, c_text, vec.tobytes()))
            insert_chunks(payload)
            self.load_or_rebuild_index()

        return {"doc_id": doc_id, "filename": safe_name, "chunks": len(chunk_rows)}

    def load_or_rebuild_index(self) -> None:
        rows = all_chunks_with_embeddings()
        self.index = faiss.IndexFlatIP(self.dim)
        mapping = []
        vectors = []
        for i, row in enumerate(rows):
            vec = np.frombuffer(row["embedding"], dtype="float32")
            vectors.append(vec)
            mapping.append((i, row["id"]))

        if vectors:
            arr = np.vstack(vectors).astype("float32")
            faiss.normalize_L2(arr)
            self.index.add(arr)
        set_faiss_mapping(mapping)

        try:
            faiss.write_index(self.index, str(FAISS_INDEX_PATH))
        except Exception:
            logger.exception("Failed to persist FAISS index")

    def remove_document(self, doc_id: int) -> bool:
        filepath = delete_document(doc_id)
        if filepath is None:
            return False
        try:
            Path(filepath).unlink(missing_ok=True)
        except Exception:
            logger.exception("Failed to delete file %s", filepath)
        self.load_or_rebuild_index()
        return True

    def retrieve(self, query: str, top_k: int) -> List[Dict]:
        if self.index.ntotal == 0:
            return []

        q = self.embed_texts([query])
        k = min(top_k, self.index.ntotal)
        scores, ids = self.index.search(q, k)
        sources = []
        for score, row_id in zip(scores[0], ids[0]):
            if row_id < 0:
                continue
            chunk_id = chunk_id_by_row(int(row_id))
            if not chunk_id:
                continue
            chunk = chunk_by_id(chunk_id)
            if not chunk:
                continue
            snippet = chunk["text"][:200]
            sources.append(
                {
                    "doc_id": chunk["doc_id"],
                    "filename": chunk["filename"],
                    "page_number": chunk["page_number"],
                    "chunk_id": chunk["id"],
                    "snippet": snippet,
                    "score": float(score),
                    "text": chunk["text"],
                }
            )
        return sources

    def build_prompt(self, question: str, contexts: List[Dict]) -> str:
        if not contexts:
            return ""
        ctx = "\n\n".join(
            [
                f"[chunk_id={c['chunk_id']}, file={c['filename']}, page={c['page_number']}]\n{c['text']}"
                for c in contexts
            ]
        )
        return (
            "You are a strict retrieval QA assistant. Use ONLY the context below. "
            "If the answer is not explicitly in the context, output exactly: "
            "I can’t find that in your documents.\n\n"
            f"Context:\n{ctx}\n\n"
            f"Question: {question}\nAnswer:"
        )
