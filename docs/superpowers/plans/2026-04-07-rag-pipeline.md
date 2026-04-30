# RAG Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an experimental RAG pipeline that ingests PDF/TXT documents, indexes them in ChromaDB using bge-m3 embeddings via Chutes, and answers questions in CLI using DeepSeek V3 via Chutes.

**Architecture:** Two CLI scripts (`ingest.py` for indexation, `ask.py` for Q&A) orchestrate small focused modules in `src/`. The `llm_client.py` module isolates all Chutes API calls so the only file to modify when migrating to other APIs (user's home APIs on another PC) is this one. ChromaDB persists locally as a folder.

**Tech Stack:** Python 3.10+, ChromaDB, pypdf, requests, python-dotenv, pytest

**Spec:** `docs/superpowers/specs/2026-04-07-rag-pipeline-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `requirements.txt` | Python dependencies |
| `.gitignore` | Exclude `.env`, `chroma_db/`, `__pycache__/`, `data/` |
| `.env.example` | Template for `CHUTES_API_TOKEN` |
| `README.md` | Setup + usage instructions |
| `src/__init__.py` | Marks `src/` as a package |
| `src/loader.py` | Read PDF + TXT from `data/` → list of normalized documents |
| `src/chunker.py` | Split documents into 800-char chunks with 100-char overlap |
| `src/llm_client.py` | Chutes API calls: `embed_texts()` and `generate()` |
| `src/vectorstore.py` | Thin ChromaDB wrapper: `add_chunks()` and `search()` |
| `src/rag.py` | RAG orchestration: embed question → search → build prompt → generate |
| `ingest.py` | CLI entry point for indexation |
| `ask.py` | CLI entry point for interactive Q&A loop |
| `tests/test_loader.py` | Unit tests for the loader (PDF + TXT) |
| `tests/test_chunker.py` | Unit tests for the chunker |
| `tests/test_rag.py` | Unit tests for prompt building and source formatting |
| `tests/fixtures/sample.txt` | Test fixture: small text file |
| `tests/fixtures/sample.pdf` | Test fixture: small PDF file |

**Testing strategy:** TDD on pure-logic modules (loader normalization, chunker, rag prompt builder). I/O-heavy modules that hit Chutes (`llm_client.py`) and ChromaDB (`vectorstore.py`) are validated by end-to-end smoke tests in Task 10 — mocking them would dominate the test code without catching real bugs in an experimental project.

---

## Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/sample.txt`

- [ ] **Step 1: Initialize git repository**

Run:
```bash
cd /root/Genialrag
git init
git config user.email "dev@genialrag.local"
git config user.name "Genialrag Dev"
```

Expected: `Initialized empty Git repository in /root/Genialrag/.git/`

- [ ] **Step 2: Create `requirements.txt`**

```
pypdf==4.3.1
chromadb==0.5.5
requests==2.32.3
python-dotenv==1.0.1
pytest==8.3.2
```

- [ ] **Step 3: Create `.gitignore`**

```
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.venv/
venv/

# Project
.env
chroma_db/
data/

# Editor
.vscode/
.idea/
*.swp
.DS_Store
```

Note: `data/` is gitignored because user documents may be sensitive. `tests/fixtures/` is NOT in `data/` so test fixtures stay tracked.

- [ ] **Step 4: Create `.env.example`**

```
# Copy this file to .env and fill in your real Chutes API token
# Get your token at https://chutes.ai
CHUTES_API_TOKEN=your_chutes_token_here
```

- [ ] **Step 5: Create empty package init files**

`src/__init__.py`:
```python
```

`tests/__init__.py`:
```python
```

- [ ] **Step 6: Create test fixture `tests/fixtures/sample.txt`**

```
Le manuel utilisateur de Genialrag décrit comment indexer des documents.
La pipeline supporte les formats PDF et TXT.
Les chunks sont stockés dans une base vectorielle ChromaDB.
```

- [ ] **Step 7: Install dependencies**

Run: `cd /root/Genialrag && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`

Expected: All packages install without error. Verify with `pip list | grep -E "chromadb|pypdf|requests"`.

- [ ] **Step 8: Commit**

```bash
cd /root/Genialrag
git add requirements.txt .gitignore .env.example src/__init__.py tests/__init__.py tests/fixtures/sample.txt
git commit -m "chore: project scaffolding (deps, gitignore, package layout)"
```

---

## Task 2: Document loader (`src/loader.py`)

**Files:**
- Create: `src/loader.py`
- Create: `tests/test_loader.py`
- Create: `tests/fixtures/sample.pdf` (generated programmatically in test setup)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_loader.py`:
```python
"""Tests for the document loader."""
from pathlib import Path

import pytest

from src.loader import load_documents


FIXTURES = Path(__file__).parent / "fixtures"


def test_load_txt_returns_single_document(tmp_path):
    """A TXT file should produce exactly one document with page=None."""
    txt = tmp_path / "note.txt"
    txt.write_text("Hello world", encoding="utf-8")

    docs = load_documents(tmp_path)

    assert len(docs) == 1
    assert docs[0]["source"] == str(txt)
    assert docs[0]["page"] is None
    assert docs[0]["text"] == "Hello world"


def test_load_pdf_returns_one_document_per_page(tmp_path):
    """A 2-page PDF should produce two documents, one per page."""
    from pypdf import PdfWriter

    pdf_path = tmp_path / "doc.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    docs = load_documents(tmp_path)

    assert len(docs) == 2
    assert all(d["source"] == str(pdf_path) for d in docs)
    assert {d["page"] for d in docs} == {1, 2}


def test_load_recursively(tmp_path):
    """Documents in subdirectories should also be loaded."""
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "deep.txt").write_text("deep content", encoding="utf-8")
    (tmp_path / "top.txt").write_text("top content", encoding="utf-8")

    docs = load_documents(tmp_path)

    assert len(docs) == 2


def test_load_ignores_unsupported_extensions(tmp_path):
    """Files like .md or .json should be silently ignored."""
    (tmp_path / "note.md").write_text("# markdown", encoding="utf-8")
    (tmp_path / "real.txt").write_text("real text", encoding="utf-8")

    docs = load_documents(tmp_path)

    assert len(docs) == 1
    assert docs[0]["text"] == "real text"


def test_load_empty_dir_returns_empty_list(tmp_path):
    """An empty directory should return [] without raising."""
    assert load_documents(tmp_path) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /root/Genialrag && . .venv/bin/activate && pytest tests/test_loader.py -v`

Expected: All 5 tests FAIL with `ModuleNotFoundError: No module named 'src.loader'`.

- [ ] **Step 3: Implement `src/loader.py`**

```python
"""Read PDF and TXT files from a directory into a uniform document format.

A document is a dict with keys:
    - source: str   (path to the file)
    - page:   int | None  (page number for PDFs, None for TXT)
    - text:   str   (raw text content)
"""
from pathlib import Path

from pypdf import PdfReader


def load_documents(data_dir: str | Path) -> list[dict]:
    """Recursively load all PDF and TXT files in `data_dir`.

    Returns a flat list of document dicts. Empty list if no supported files.
    """
    data_dir = Path(data_dir)
    docs: list[dict] = []

    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".txt":
            docs.append(_load_txt(path))
        elif suffix == ".pdf":
            docs.extend(_load_pdf(path))

    return docs


def _load_txt(path: Path) -> dict:
    return {
        "source": str(path),
        "page": None,
        "text": path.read_text(encoding="utf-8"),
    }


def _load_pdf(path: Path) -> list[dict]:
    reader = PdfReader(str(path))
    out = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        out.append({
            "source": str(path),
            "page": i,
            "text": text,
        })
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /root/Genialrag && . .venv/bin/activate && pytest tests/test_loader.py -v`

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /root/Genialrag
git add src/loader.py tests/test_loader.py
git commit -m "feat: document loader for PDF and TXT files"
```

---

## Task 3: Chunker (`src/chunker.py`)

**Files:**
- Create: `src/chunker.py`
- Create: `tests/test_chunker.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_chunker.py`:
```python
"""Tests for the document chunker."""
from src.chunker import chunk_documents


def test_short_document_yields_single_chunk():
    """A document shorter than chunk_size produces exactly one chunk."""
    docs = [{"source": "a.txt", "page": None, "text": "Hello world"}]

    chunks = chunk_documents(docs, chunk_size=800, overlap=100)

    assert len(chunks) == 1
    assert chunks[0]["text"] == "Hello world"
    assert chunks[0]["source"] == "a.txt"
    assert chunks[0]["page"] is None
    assert chunks[0]["chunk_id"] == "a.txt_pNone_c0"


def test_long_document_is_split():
    """A 2000-char document with chunk_size=800 yields multiple chunks."""
    text = "x" * 2000
    docs = [{"source": "big.txt", "page": None, "text": text}]

    chunks = chunk_documents(docs, chunk_size=800, overlap=100)

    assert len(chunks) >= 2
    # Each chunk (except possibly the last) is exactly chunk_size chars
    for c in chunks[:-1]:
        assert len(c["text"]) == 800


def test_overlap_between_consecutive_chunks():
    """Chunks should overlap by `overlap` characters."""
    text = "abcdefghij" * 100  # 1000 chars
    docs = [{"source": "x.txt", "page": None, "text": text}]

    chunks = chunk_documents(docs, chunk_size=300, overlap=50)

    # The end of chunk[0] should match the start of chunk[1] by `overlap` chars
    assert chunks[0]["text"][-50:] == chunks[1]["text"][:50]


def test_chunk_ids_are_unique_and_stable():
    """Same input → same chunk_ids, all unique."""
    docs = [
        {"source": "a.pdf", "page": 1, "text": "x" * 1500},
        {"source": "a.pdf", "page": 2, "text": "y" * 1500},
    ]

    chunks = chunk_documents(docs, chunk_size=800, overlap=100)
    ids = [c["chunk_id"] for c in chunks]

    assert len(ids) == len(set(ids))  # all unique
    assert ids[0] == "a.pdf_p1_c0"


def test_metadata_preserved_per_chunk():
    """Source and page from the parent document are preserved on each chunk."""
    docs = [{"source": "manuel.pdf", "page": 7, "text": "z" * 2000}]

    chunks = chunk_documents(docs, chunk_size=800, overlap=100)

    assert all(c["source"] == "manuel.pdf" for c in chunks)
    assert all(c["page"] == 7 for c in chunks)


def test_empty_text_yields_no_chunks():
    """A document with empty text produces zero chunks."""
    docs = [{"source": "empty.txt", "page": None, "text": ""}]

    chunks = chunk_documents(docs, chunk_size=800, overlap=100)

    assert chunks == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /root/Genialrag && . .venv/bin/activate && pytest tests/test_chunker.py -v`

Expected: All 6 tests FAIL with `ModuleNotFoundError: No module named 'src.chunker'`.

- [ ] **Step 3: Implement `src/chunker.py`**

```python
"""Split documents into overlapping fixed-size chunks.

A chunk is a dict with keys:
    - chunk_id: str   (unique stable id)
    - source:   str
    - page:     int | None
    - text:     str
"""


def chunk_documents(
    docs: list[dict],
    chunk_size: int = 800,
    overlap: int = 100,
) -> list[dict]:
    """Split each document into chunks of `chunk_size` chars with `overlap`.

    Returns a flat list of chunk dicts.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[dict] = []
    for doc in docs:
        chunks.extend(_chunk_one(doc, chunk_size, overlap))
    return chunks


def _chunk_one(doc: dict, chunk_size: int, overlap: int) -> list[dict]:
    text = doc["text"]
    if not text:
        return []

    step = chunk_size - overlap
    out = []
    i = 0
    chunk_index = 0
    while i < len(text):
        piece = text[i : i + chunk_size]
        out.append({
            "chunk_id": f"{doc['source']}_p{doc['page']}_c{chunk_index}",
            "source": doc["source"],
            "page": doc["page"],
            "text": piece,
        })
        chunk_index += 1
        if i + chunk_size >= len(text):
            break
        i += step
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /root/Genialrag && . .venv/bin/activate && pytest tests/test_chunker.py -v`

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /root/Genialrag
git add src/chunker.py tests/test_chunker.py
git commit -m "feat: text chunker with configurable size and overlap"
```

---

## Task 4: Chutes LLM client (`src/llm_client.py`)

**Files:**
- Create: `src/llm_client.py`

No unit tests for this module — it hits the real Chutes API. Validation happens in Task 10 (end-to-end smoke test).

- [ ] **Step 1: Implement `src/llm_client.py`**

```python
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

CHUTES_API_TOKEN = os.getenv("CHUTES_API_TOKEN")

EMBED_URL = "https://chutes-baai-bge-m3.chutes.ai/v1/embeddings"
GEN_URL = "https://llm.chutes.ai/v1/chat/completions"
GEN_MODEL = "deepseek-ai/DeepSeek-V3-0324-TEE"

EMBED_DIM = 1024  # bge-m3 dimension
REQUEST_TIMEOUT = 60  # seconds


def _check_token() -> None:
    if not CHUTES_API_TOKEN:
        raise RuntimeError(
            "CHUTES_API_TOKEN is not set. Create a .env file at the project "
            "root with: CHUTES_API_TOKEN=your_token_here"
        )


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {CHUTES_API_TOKEN}",
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
    """Generate a text response from the LLM (DeepSeek V3 via Chutes).

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
```

- [ ] **Step 2: Smoke-check that the module imports**

Run: `cd /root/Genialrag && . .venv/bin/activate && python -c "from src.llm_client import embed_texts, generate; print('OK')"`

Expected: `OK` (no import errors). Functions are not called yet — that happens in Task 10.

- [ ] **Step 3: Commit**

```bash
cd /root/Genialrag
git add src/llm_client.py
git commit -m "feat: Chutes API client for bge-m3 embeddings and DeepSeek V3 generation"
```

---

## Task 5: Vector store (`src/vectorstore.py`)

**Files:**
- Create: `src/vectorstore.py`

No unit test — ChromaDB is exercised in the end-to-end smoke test (Task 10).

- [ ] **Step 1: Implement `src/vectorstore.py`**

```python
"""Thin wrapper around ChromaDB for the RAG pipeline.

Encapsulates the only two operations we need:
    - add_chunks: store chunks with their precomputed embeddings
    - search:     find the top-k chunks closest to a query embedding

The wrapper exists so we can swap ChromaDB for another vector DB later
(Qdrant, sqlite-vec, etc.) without touching the rest of the codebase.
"""
from pathlib import Path

import chromadb


COLLECTION_NAME = "documents"


class VectorStore:
    def __init__(self, persist_dir: str | Path = "chroma_db"):
        self.persist_dir = str(persist_dir)
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME
        )

    def add_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        """Insert (or upsert) chunks with their precomputed embeddings.

        Uses chunk_id as the Chroma id, so re-indexing the same source file
        overwrites existing chunks instead of duplicating them.
        """
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "source": c["source"],
                # ChromaDB metadata doesn't support None — store -1 sentinel
                "page": c["page"] if c["page"] is not None else -1,
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
    ) -> list[dict]:
        """Return the top_k chunks closest to query_embedding.

        Each result is a dict: {chunk_id, source, page, text, distance}.
        Sorted from most relevant (smallest distance) to least.
        """
        if self.collection.count() == 0:
            return []

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        out = []
        for i in range(len(result["ids"][0])):
            meta = result["metadatas"][0][i]
            page = meta["page"] if meta["page"] != -1 else None
            out.append({
                "chunk_id": result["ids"][0][i],
                "source": meta["source"],
                "page": page,
                "text": result["documents"][0][i],
                "distance": result["distances"][0][i],
            })
        return out

    def count(self) -> int:
        """Total number of chunks currently stored."""
        return self.collection.count()
```

- [ ] **Step 2: Smoke-check that the module imports**

Run: `cd /root/Genialrag && . .venv/bin/activate && python -c "from src.vectorstore import VectorStore; print('OK')"`

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
cd /root/Genialrag
git add src/vectorstore.py
git commit -m "feat: ChromaDB wrapper with upsert by chunk_id"
```

---

## Task 6: RAG logic (`src/rag.py`)

**Files:**
- Create: `src/rag.py`
- Create: `tests/test_rag.py`

We test the pure functions (`build_prompt`, `format_sources`) without hitting any external API. The orchestration function `answer_question` is exercised in Task 10.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_rag.py`:
```python
"""Tests for the RAG orchestration helpers."""
from src.rag import build_prompt, format_sources


def test_build_prompt_includes_question():
    chunks = [
        {"source": "manuel.pdf", "page": 3, "text": "Le RAG fonctionne ainsi."},
    ]
    prompt = build_prompt("Comment fonctionne le RAG ?", chunks)

    assert "Comment fonctionne le RAG ?" in prompt
    assert "Le RAG fonctionne ainsi." in prompt


def test_build_prompt_includes_all_chunks_with_sources():
    chunks = [
        {"source": "a.pdf", "page": 1, "text": "Premier extrait."},
        {"source": "b.txt", "page": None, "text": "Second extrait."},
    ]
    prompt = build_prompt("Une question ?", chunks)

    assert "Premier extrait." in prompt
    assert "Second extrait." in prompt
    assert "a.pdf" in prompt
    assert "b.txt" in prompt
    assert "page 1" in prompt


def test_build_prompt_instructs_to_say_idk():
    """The prompt must tell the model to say 'Je ne sais pas' if no answer."""
    prompt = build_prompt("Q ?", [])

    assert "Je ne sais pas" in prompt


def test_format_sources_compact():
    chunks = [
        {"source": "data/manuel.pdf", "page": 3, "text": "..."},
        {"source": "data/guide.txt",  "page": None, "text": "..."},
        {"source": "data/manuel.pdf", "page": 7, "text": "..."},
    ]

    formatted = format_sources(chunks)

    assert "manuel.pdf (page 3)" in formatted
    assert "guide.txt" in formatted
    assert "manuel.pdf (page 7)" in formatted


def test_format_sources_empty():
    assert format_sources([]) == "Sources : aucune"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /root/Genialrag && . .venv/bin/activate && pytest tests/test_rag.py -v`

Expected: All 5 tests FAIL with `ModuleNotFoundError: No module named 'src.rag'`.

- [ ] **Step 3: Implement `src/rag.py`**

```python
"""RAG orchestration: question → retrieval → prompt → generation."""
from pathlib import Path

from src.llm_client import embed_texts, generate
from src.vectorstore import VectorStore


PROMPT_TEMPLATE = """Tu es un assistant qui répond à des questions en te basant UNIQUEMENT sur les extraits de documentation fournis ci-dessous.
Si la réponse n'est pas dans les extraits, dis "Je ne sais pas".
Cite les sources sous la forme [source: nom_fichier, page X].

EXTRAITS :
{extraits}

QUESTION : {question}

RÉPONSE :"""


def build_prompt(question: str, chunks: list[dict]) -> str:
    """Assemble the final prompt sent to the LLM."""
    if chunks:
        parts = []
        for i, c in enumerate(chunks, start=1):
            source_label = Path(c["source"]).name
            if c["page"] is not None:
                header = f"[Extrait {i} — source: {source_label}, page {c['page']}]"
            else:
                header = f"[Extrait {i} — source: {source_label}]"
            parts.append(f"---\n{header}\n{c['text']}")
        extraits = "\n".join(parts) + "\n---"
    else:
        extraits = "(aucun extrait disponible)"

    return PROMPT_TEMPLATE.format(extraits=extraits, question=question)


def format_sources(chunks: list[dict]) -> str:
    """Format the list of sources for display under the answer."""
    if not chunks:
        return "Sources : aucune"

    lines = ["Sources :"]
    for c in chunks:
        name = Path(c["source"]).name
        if c["page"] is not None:
            lines.append(f"  - {name} (page {c['page']})")
        else:
            lines.append(f"  - {name}")
    return "\n".join(lines)


def answer_question(
    question: str,
    vectorstore: VectorStore,
    top_k: int = 4,
) -> dict:
    """Run the full RAG pipeline for a single question.

    Returns: {"answer": str, "sources": list[dict]}
    """
    query_vec = embed_texts([question])[0]
    chunks = vectorstore.search(query_vec, top_k=top_k)
    prompt = build_prompt(question, chunks)
    answer = generate(prompt)
    return {"answer": answer, "sources": chunks}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /root/Genialrag && . .venv/bin/activate && pytest tests/test_rag.py -v`

Expected: All 5 tests PASS.

- [ ] **Step 5: Run the full test suite**

Run: `cd /root/Genialrag && . .venv/bin/activate && pytest -v`

Expected: All tests from Tasks 2, 3, and 6 PASS (16 tests total).

- [ ] **Step 6: Commit**

```bash
cd /root/Genialrag
git add src/rag.py tests/test_rag.py
git commit -m "feat: RAG orchestration with prompt builder and source formatter"
```

---

## Task 7: Indexation CLI (`ingest.py`)

**Files:**
- Create: `ingest.py`

- [ ] **Step 1: Implement `ingest.py`**

```python
"""CLI: index documents from a directory into the vector store.

Usage:
    python ingest.py
    python ingest.py --data-dir other_docs/
"""
import argparse
import sys
import time
from pathlib import Path

from src.chunker import chunk_documents
from src.llm_client import embed_texts
from src.loader import load_documents
from src.vectorstore import VectorStore


EMBED_BATCH_SIZE = 32


def main() -> int:
    parser = argparse.ArgumentParser(description="Index documents into ChromaDB.")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory containing PDF/TXT files to index (default: data/)",
    )
    parser.add_argument(
        "--persist-dir",
        default="chroma_db",
        help="Directory where ChromaDB persists (default: chroma_db/)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: data directory '{data_dir}' does not exist.", file=sys.stderr)
        return 1

    start = time.time()

    print(f"Loading documents from {data_dir}/ ...")
    docs = load_documents(data_dir)
    if not docs:
        print("No PDF or TXT files found. Nothing to index.")
        return 0
    print(f"  loaded {len(docs)} document entries")

    print("Chunking ...")
    chunks = chunk_documents(docs)
    print(f"  produced {len(chunks)} chunks")

    if not chunks:
        print("No chunks produced (empty documents?). Nothing to index.")
        return 0

    print(f"Embedding {len(chunks)} chunks via Chutes (batch size {EMBED_BATCH_SIZE}) ...")
    all_embeddings: list[list[float]] = []
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        texts = [c["text"] for c in batch]
        vectors = embed_texts(texts)
        all_embeddings.extend(vectors)
        print(f"  embedded {min(i + EMBED_BATCH_SIZE, len(chunks))}/{len(chunks)}")

    print("Storing in ChromaDB ...")
    store = VectorStore(persist_dir=args.persist_dir)
    store.add_chunks(chunks, all_embeddings)

    elapsed = time.time() - start
    n_files = len({c["source"] for c in chunks})
    print(
        f"\nDone. Indexed {len(chunks)} chunks from {n_files} files "
        f"in {elapsed:.1f}s. Total chunks in store: {store.count()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Verify the script parses arguments correctly**

Run: `cd /root/Genialrag && . .venv/bin/activate && python ingest.py --help`

Expected: argparse help text shows `--data-dir` and `--persist-dir` options.

- [ ] **Step 3: Commit**

```bash
cd /root/Genialrag
git add ingest.py
git commit -m "feat: ingest.py CLI for batch indexation"
```

---

## Task 8: Question CLI (`ask.py`)

**Files:**
- Create: `ask.py`

- [ ] **Step 1: Implement `ask.py`**

```python
"""CLI: interactive Q&A loop over the indexed documents.

Each question is independent (one-shot, no conversational memory).
Exit by typing 'quit' or pressing Ctrl+C.

Usage:
    python ask.py
"""
import sys
from pathlib import Path

from src.rag import answer_question, format_sources
from src.vectorstore import VectorStore


PERSIST_DIR = "chroma_db"


def main() -> int:
    if not Path(PERSIST_DIR).exists():
        print(
            f"Error: vector store '{PERSIST_DIR}/' does not exist.\n"
            f"Run 'python ingest.py' first to index your documents.",
            file=sys.stderr,
        )
        return 1

    store = VectorStore(persist_dir=PERSIST_DIR)
    if store.count() == 0:
        print(
            "Vector store is empty. Run 'python ingest.py' first to index "
            "your documents.",
            file=sys.stderr,
        )
        return 1

    print(f"Genialrag — {store.count()} chunks indexed. Type 'quit' to exit.\n")

    while True:
        try:
            question = input("Question > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            break

        try:
            result = answer_question(question, store)
        except Exception as e:
            print(f"Error: {e}\n", file=sys.stderr)
            continue

        print()
        print("Réponse :")
        print(result["answer"])
        print()
        print(format_sources(result["sources"]))
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Verify the script imports correctly**

Run: `cd /root/Genialrag && . .venv/bin/activate && python -c "import ask; print('OK')"`

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
cd /root/Genialrag
git add ask.py
git commit -m "feat: ask.py CLI with interactive one-shot Q&A loop"
```

---

## Task 9: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
# Genialrag

Pipeline RAG (Retrieval-Augmented Generation) expérimentale pour poser des
questions à une base documentaire (PDF + TXT). Indexation locale via ChromaDB,
embeddings `bge-m3` et génération `DeepSeek-V3-0324-TEE` via Chutes.

## Prérequis

- Python 3.10+
- Un compte [Chutes](https://chutes.ai) avec une clé API
- Les modèles `BAAI/bge-m3` et `deepseek-ai/DeepSeek-V3-0324-TEE` accessibles
  sur ton compte Chutes

## Installation

```bash
git clone <repo>
cd Genialrag
python -m venv .venv
source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Crée un fichier `.env` à la racine du projet :

```
CHUTES_API_TOKEN=ton_token_chutes_ici
```

(Tu peux copier `.env.example` comme point de départ.)

## Utilisation

### 1. Mettre des documents dans `data/`

```bash
mkdir -p data
cp /chemin/vers/mes_documents/*.pdf data/
cp /chemin/vers/mes_documents/*.txt data/
```

### 2. Indexer

```bash
python ingest.py
```

Cela va lire tous les PDF/TXT de `data/`, les découper en chunks, calculer les
embeddings via Chutes, et les stocker dans `chroma_db/`. Les ré-indexations
suivantes écrasent les chunks existants (pas de doublons).

### 3. Poser des questions

```bash
python ask.py
```

Cela ouvre une boucle interactive. Chaque question est traitée indépendamment
(pas de mémoire conversationnelle pour le moment). Tape `quit` ou `Ctrl+C` pour
sortir.

## Structure

```
Genialrag/
├── data/                # Tes PDF et TXT (gitignored)
├── chroma_db/           # Base vectorielle persistée (auto-générée, gitignored)
├── src/
│   ├── loader.py        # Lecture PDF + TXT
│   ├── chunker.py       # Découpage en chunks
│   ├── llm_client.py    # Appels Chutes (← seul fichier à modifier pour
│   │                    #   pointer vers d'autres APIs)
│   ├── vectorstore.py   # Wrapper ChromaDB
│   └── rag.py           # Logique RAG (retrieval + prompt + génération)
├── ingest.py            # CLI d'indexation
├── ask.py               # CLI de questions
└── tests/               # Tests unitaires (pytest)
```

## Tests

```bash
pytest -v
```

## Migration vers d'autres APIs

Pour utiliser d'autres APIs (par exemple les APIs maison sur un autre PC),
modifie uniquement `src/llm_client.py` :

- Mets à jour `EMBED_URL`, `GEN_URL`, `GEN_MODEL`
- Si l'API n'est pas OpenAI-compatible, ajuste le parsing des réponses JSON
  dans `embed_texts()` et `generate()`
- Adapte la variable d'environnement utilisée pour le token si nécessaire

Aucun autre fichier n'a besoin d'être modifié.
```

- [ ] **Step 2: Commit**

```bash
cd /root/Genialrag
git add README.md
git commit -m "docs: README with setup, usage, and migration guide"
```

---

## Task 10: End-to-end smoke test

**Files:** None created. This is a manual validation that the full pipeline works against the real Chutes API.

**Prerequisite:** A real `CHUTES_API_TOKEN` must be available. The user must create the `.env` file before running this task.

- [ ] **Step 1: Verify the `.env` file exists and is loadable**

Run: `cd /root/Genialrag && . .venv/bin/activate && python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('TOKEN OK' if os.getenv('CHUTES_API_TOKEN') else 'NO TOKEN')"`

Expected: `TOKEN OK`. If `NO TOKEN`, stop and ask the user to create `.env` with their real token.

- [ ] **Step 2: Prepare a small test corpus**

Run:
```bash
cd /root/Genialrag
mkdir -p data
cp tests/fixtures/sample.txt data/sample.txt
```

This places the test fixture into `data/` so `ingest.py` has something to chew on. The fixture mentions Genialrag, the PDF/TXT pipeline, and ChromaDB, which gives us specific facts to ask about.

- [ ] **Step 3: Run indexation against real Chutes**

Run: `cd /root/Genialrag && . .venv/bin/activate && python ingest.py`

Expected output (approximately):
```
Loading documents from data/ ...
  loaded 1 document entries
Chunking ...
  produced 1 chunks
Embedding 1 chunks via Chutes (batch size 32) ...
  embedded 1/1
Storing in ChromaDB ...

Done. Indexed 1 chunks from 1 files in <some>s. Total chunks in store: 1
```

If the Chutes API call fails, read the error message — it includes the HTTP status and response body. Common issues: invalid token, model not enabled on the account, network blocked.

- [ ] **Step 4: Verify ChromaDB persistence on disk**

Run: `ls -la /root/Genialrag/chroma_db/`

Expected: directory exists, contains a `chroma.sqlite3` file and possibly subdirectories for the collection.

- [ ] **Step 5: Run the question CLI and ask a test question**

Run: `cd /root/Genialrag && . .venv/bin/activate && python ask.py`

When the prompt appears, type:
```
Quels formats la pipeline supporte-t-elle ?
```

Expected:
- A `Réponse :` block containing text mentioning PDF and TXT (the LLM should ground its answer in the indexed chunk).
- A `Sources :` block listing `sample.txt`.
- The prompt returns for another question.

Then type `quit` and hit Enter to exit.

- [ ] **Step 6: Verify re-indexation does not duplicate**

Run: `cd /root/Genialrag && . .venv/bin/activate && python ingest.py`

Expected: the final line still shows `Total chunks in store: 1` (not 2). This confirms upsert-by-chunk_id works.

- [ ] **Step 7: Final commit**

If everything works, there are no code changes to commit (this task only validates). Just verify clean state:

```bash
cd /root/Genialrag
git status
```

Expected: working tree clean (the `data/` and `chroma_db/` artifacts are gitignored).

If any code adjustments were needed during smoke testing (for example, fixing an unexpected response format from Chutes), commit them now with an appropriate message:

```bash
git add <modified files>
git commit -m "fix: <what was adjusted>"
```

---

## Done

The pipeline is functional end-to-end. Next steps from the spec's "Évolutions envisagées" section can be picked up as separate plans:

- Streaming responses
- Multi-turn conversation memory
- Additional file formats (docx, html)
- Smarter chunking strategies
- Web UI / Windows desktop app (long-term production target)
