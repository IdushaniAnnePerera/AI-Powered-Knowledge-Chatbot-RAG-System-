# AI-Powered Knowledge Chatbot (Local RAG)

A fully local Retrieval-Augmented Generation chatbot that answers only from user-uploaded documents.

## Features
- Upload `.pdf`, `.txt`, `.md` files (max 20MB)
- PDF extraction with page numbers via PyMuPDF
- Chunking + embeddings using sentence-transformers
- FAISS vector search with cosine similarity (normalized vectors)
- Grounded chat answers via local Ollama model
- Strict fallback: `I can’t find that in your documents.`
- Citations returned with `filename`, `page_number`, `chunk_id`, `snippet`
- SQLite persistence for docs, chunks, FAISS row mappings, and chat history
- React + Tailwind chat UI with session persistence in `localStorage`

## Project Structure

- `backend/app/main.py`
- `backend/app/rag.py`
- `backend/app/storage.py`
- `backend/app/ollama_client.py`
- `backend/app/models.py`
- `backend/app/config.py`
- `backend/requirements.txt`
- `frontend/src/...`
- `samples/`

## 1) Start Ollama

```bash
ollama pull llama3.1:8b
ollama serve
```

## 2) Start backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 3) Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

## 4) Upload a PDF
Use the upload control in the left panel.

## 5) Ask a question and see citations
Ask in the center chat panel. The right panel shows sources used in the latest answer.

## API
- `POST /upload`
- `GET /docs`
- `DELETE /docs/{doc_id}`
- `POST /chat`
- `GET /chat/{session_id}`
- `DELETE /chat/{session_id}`
- `GET /health`

## Quick demo ingest

```bash
cd backend
python ingest_samples.py
```

## Notes
- No paid API is used.
- If Ollama is offline, `/chat` returns a friendly message with startup steps.
