# Backend (FastAPI RAG)

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Quick ingest sample docs

```bash
cd backend
python ingest_samples.py
```
