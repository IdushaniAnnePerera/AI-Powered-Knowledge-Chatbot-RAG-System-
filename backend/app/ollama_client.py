from typing import Optional

import requests

from .config import OLLAMA_MODEL, OLLAMA_URL


class OllamaUnavailableError(Exception):
    pass


def check_ollama() -> bool:
    try:
        res = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return res.ok
    except requests.RequestException:
        return False


def generate_answer(prompt: str, model: Optional[str] = None) -> str:
    payload = {"model": model or OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        res = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=90)
    except requests.RequestException as exc:
        raise OllamaUnavailableError(
            "Ollama is not reachable. Start it with `ollama serve` and pull a model with `ollama pull llama3.1:8b`."
        ) from exc

    if not res.ok:
        raise OllamaUnavailableError(
            f"Ollama error ({res.status_code}). Ensure `ollama serve` is running and model `{payload['model']}` exists."
        )

    data = res.json()
    return data.get("response", "").strip()
