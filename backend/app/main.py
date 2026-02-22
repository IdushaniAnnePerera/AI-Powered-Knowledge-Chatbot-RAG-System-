import logging
import uuid
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import EMBED_MODEL, MAX_UPLOAD_MB, TOP_K, ensure_dirs
from .models import ChatRequest, ChatResponse, HealthResponse
from .ollama_client import OllamaUnavailableError, check_ollama, generate_answer
from .rag import RAGService
from .storage import (
    add_chat_message,
    clear_chat_history,
    counts,
    get_chat_history,
    init_db,
    list_documents,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Knowledge Chatbot (RAG)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_dirs()
init_db()
rag = RAGService()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    docs_count, chunks_count = counts()
    return HealthResponse(
        status="ok",
        ollama_ok=check_ollama(),
        embed_model=EMBED_MODEL,
        docs_count=docs_count,
        chunks_count=chunks_count,
    )


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    data = await file.read()
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_UPLOAD_MB}MB limit")
    try:
        result = rag.upload_document(file.filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail="Failed to process document") from exc
    return result


@app.get("/docs")
def docs() -> Dict[str, Any]:
    return {"documents": list_documents()}


@app.delete("/docs/{doc_id}")
def delete_doc(doc_id: int) -> Dict[str, Any]:
    ok = rag.remove_document(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "doc_id": doc_id}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    top_k = req.top_k or TOP_K
    session_id = req.session_id or str(uuid.uuid4())

    add_chat_message(session_id, "user", req.message)

    retrieved = rag.retrieve(req.message, top_k=top_k)
    if not retrieved:
        answer = "I can’t find that in your documents."
        add_chat_message(session_id, "assistant", answer)
        return ChatResponse(answer=answer, sources=[], session_id=session_id)

    prompt = rag.build_prompt(req.message, retrieved)
    try:
        answer = generate_answer(prompt)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not answer or "I can’t find that in your documents." in answer:
        answer = "I can’t find that in your documents."

    add_chat_message(session_id, "assistant", answer)
    sources = [
        {
            "doc_id": s["doc_id"],
            "filename": s["filename"],
            "page_number": s["page_number"],
            "chunk_id": s["chunk_id"],
            "snippet": s["snippet"],
        }
        for s in retrieved
    ]
    return ChatResponse(answer=answer, sources=sources, session_id=session_id)


@app.get("/chat/{session_id}")
def chat_history(session_id: str) -> Dict[str, Any]:
    return {"session_id": session_id, "messages": get_chat_history(session_id)}


@app.delete("/chat/{session_id}")
def clear_chat(session_id: str) -> Dict[str, Any]:
    clear_chat_history(session_id)
    return {"status": "cleared", "session_id": session_id}
