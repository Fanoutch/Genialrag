"""Client for the Chutes API.

Exposes two functions:
    - embed_texts(texts) -> list of embedding vectors (1024-dim for bge-m3)
    - generate(prompt)   -> generated text response

This is the ONLY file to modify when migrating to other APIs (e.g. user's
home APIs on another PC). If the target API is OpenAI-compatible, only the
URL constants and possibly the model name need to change. Otherwise the
parsing of the JSON response also needs to be adapted.
"""
import os

import requests
from dotenv import load_dotenv

# Load .env file if present (no error if missing — variables can also come
# from the actual environment)
load_dotenv()

CHUTES_API_KEY = os.getenv("CHUTES_API_KEY")

EMBED_URL = "https://chutes-baai-bge-m3.chutes.ai/v1/embeddings"
GEN_URL = "https://llm.chutes.ai/v1/chat/completions"
GEN_MODEL = "unsloth/Mistral-Nemo-Instruct-2407"

EMBED_DIM = 1024  # bge-m3 dimension
REQUEST_TIMEOUT = 60  # seconds


def _check_token() -> None:
    if not CHUTES_API_KEY:
        raise RuntimeError(
            "CHUTES_API_KEY is not set. Create a .env file at the project "
            "root with: CHUTES_API_KEY=your_token_here"
        )


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json",
    }


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using bge-m3 via Chutes.

    Returns a list of 1024-dimensional vectors in the same order as inputs.
    """
    _check_token()
    if not texts:
        return []

    payload = {"input": texts, "model": None}
    resp = requests.post(
        EMBED_URL,
        headers=_headers(),
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Embedding API error {resp.status_code}: {resp.text}"
        )

    data = resp.json()
    # OpenAI-compatible format: {"data": [{"embedding": [...]}, ...]}
    return [item["embedding"] for item in data["data"]]


def generate(prompt: str) -> str:
    """Generate a text response from the LLM (Mistral Nemo via Chutes).

    Returns the generated text as a single string.
    """
    _check_token()

    payload = {
        "model": GEN_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0.3,
    }
    resp = requests.post(
        GEN_URL,
        headers=_headers(),
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Generation API error {resp.status_code}: {resp.text}"
        )

    data = resp.json()
    # OpenAI-compatible format
    return data["choices"][0]["message"]["content"]
