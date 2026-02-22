from typing import List, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    doc_id: int
    filename: str
    page_number: Optional[int] = None
    chunk_id: str
    snippet: str


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    session_id: str


class HealthResponse(BaseModel):
    status: str
    ollama_ok: bool
    embed_model: str
    docs_count: int
    chunks_count: int
