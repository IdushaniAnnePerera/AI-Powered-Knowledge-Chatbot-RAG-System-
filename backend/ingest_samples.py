from pathlib import Path

from app.rag import RAGService
from app.storage import init_db
from app.config import ensure_dirs


def main() -> None:
    ensure_dirs()
    init_db()
    rag = RAGService()
    samples = Path(__file__).resolve().parent.parent / "samples"
    for path in samples.iterdir():
        if path.suffix.lower() in {".pdf", ".txt", ".md"}:
            result = rag.upload_document(path.name, path.read_bytes())
            print(f"Indexed: {result}")


if __name__ == "__main__":
    main()
