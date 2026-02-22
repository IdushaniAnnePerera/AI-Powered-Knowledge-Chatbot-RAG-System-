import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config import DB_PATH, ensure_dirs


def init_db() -> None:
    ensure_dirs()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id INTEGER NOT NULL,
                page_number INTEGER,
                text TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS faiss_map (
                row_id INTEGER PRIMARY KEY,
                chunk_id TEXT NOT NULL,
                FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


@contextmanager
def get_conn() -> Iterable[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def create_document(filename: str, filepath: Path) -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO documents (filename, filepath, created_at) VALUES (?, ?, ?)",
            (filename, str(filepath), now),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_documents() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, filename, filepath, created_at FROM documents ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_document(doc_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None


def delete_document(doc_id: int) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute("SELECT filepath FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            return None
        filepath = row["filepath"]
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        return filepath


def insert_chunks(chunks: List[Tuple[str, int, Optional[int], str, bytes]]) -> None:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO chunks (id, doc_id, page_number, text, embedding, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [(cid, did, page, text, emb, now) for cid, did, page, text, emb in chunks],
        )
        conn.commit()


def all_chunks_with_embeddings() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, doc_id, page_number, text, embedding FROM chunks ORDER BY created_at, id"
        ).fetchall()


def set_faiss_mapping(mapping: List[Tuple[int, str]]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM faiss_map")
        conn.executemany("INSERT INTO faiss_map (row_id, chunk_id) VALUES (?, ?)", mapping)
        conn.commit()


def chunk_by_id(chunk_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT c.id, c.doc_id, c.page_number, c.text, d.filename
            FROM chunks c JOIN documents d ON c.doc_id = d.id
            WHERE c.id = ?
            """,
            (chunk_id,),
        ).fetchone()
        return dict(row) if row else None


def chunk_id_by_row(row_id: int) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute("SELECT chunk_id FROM faiss_map WHERE row_id = ?", (row_id,)).fetchone()
        return row["chunk_id"] if row else None


def counts() -> Tuple[int, int]:
    with get_conn() as conn:
        docs_count = conn.execute("SELECT COUNT(*) as c FROM documents").fetchone()["c"]
        chunks_count = conn.execute("SELECT COUNT(*) as c FROM chunks").fetchone()["c"]
        return docs_count, chunks_count


def add_chat_message(session_id: str, role: str, content: str) -> None:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        conn.commit()


def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM chat_messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def clear_chat_history(session_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        conn.commit()
