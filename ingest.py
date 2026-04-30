"""CLI: index documents from a directory into the vector store.

Two modes are supported, auto-detected from the structure of `--data-dir` :

1. SECTOR MODE (recommended) — `data/` contains subdirectories, each
   subdirectory is treated as a sector and gets its own ChromaDB collection.
   Example layout:
        data/
        ├── medical/        → collection "medical"
        ├── comptabilite/   → collection "comptabilite"
        └── ...

2. FLAT MODE (fallback) — `data/` directly contains files, all chunks go
   into a single "documents" collection. Kept for backward compatibility.

Usage:
    python ingest.py
    python ingest.py --data-dir other_docs/

This script is incremental: re-running it on the same data costs zero API
calls. It compares the hash of each chunk against what is already in each
collection and only embeds chunks that are new or whose content has changed.
Chunks present but no longer generated (deleted/renamed/shortened source
files) are removed at the end.
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


def ingest_sector(
    sector_dir: Path,
    collection_name: str,
    persist_dir: str,
) -> tuple[int, int, int, int]:
    """Ingest one sector directory into one ChromaDB collection.

    Returns (n_files, n_embedded, n_skipped, n_orphans_removed).
    """
    print(f"\n[{collection_name}] Loading documents from {sector_dir}/ ...")
    docs = load_documents(sector_dir)
    if not docs:
        print(f"[{collection_name}] No PDF or TXT files found, skipping.")
        return (0, 0, 0, 0)
    print(f"[{collection_name}]   loaded {len(docs)} document entries")

    chunks = chunk_documents(docs)
    print(f"[{collection_name}]   produced {len(chunks)} chunks")
    if not chunks:
        return (0, 0, 0, 0)

    store = VectorStore(persist_dir=persist_dir, collection_name=collection_name)
    existing_hashes = store.get_existing_hashes()
    print(f"[{collection_name}]   {len(existing_hashes)} chunks already in store")

    # Decide what to embed (new or changed) vs skip (unchanged).
    current_ids: set[str] = set()
    chunks_to_embed: list[dict] = []
    for chunk in chunks:
        current_ids.add(chunk["chunk_id"])
        if existing_hashes.get(chunk["chunk_id"]) == chunk["hash"]:
            continue
        chunks_to_embed.append(chunk)

    n_skipped = len(chunks) - len(chunks_to_embed)
    print(
        f"[{collection_name}] Plan: {len(chunks_to_embed)} to embed, "
        f"{n_skipped} unchanged (skipped)"
    )

    if chunks_to_embed:
        all_embeddings: list[list[float]] = []
        for i in range(0, len(chunks_to_embed), EMBED_BATCH_SIZE):
            batch = chunks_to_embed[i : i + EMBED_BATCH_SIZE]
            texts = [c["text"] for c in batch]
            vectors = embed_texts(texts)
            all_embeddings.extend(vectors)
            print(
                f"[{collection_name}]   embedded "
                f"{min(i + EMBED_BATCH_SIZE, len(chunks_to_embed))}"
                f"/{len(chunks_to_embed)}"
            )
        store.add_chunks(chunks_to_embed, all_embeddings)

    # Cleanup orphans: chunks present in the collection that we did NOT
    # regenerate this run (deleted/renamed/shortened source files).
    orphans = sorted(set(existing_hashes.keys()) - current_ids)
    if orphans:
        print(f"[{collection_name}] Removing {len(orphans)} orphan chunks ...")
        store.delete(orphans)

    n_files = len({c["source"] for c in chunks})
    print(
        f"[{collection_name}] Done. Total chunks now: {store.count()} "
        f"(from {n_files} files)"
    )
    return (n_files, len(chunks_to_embed), n_skipped, len(orphans))


def main() -> int:
    parser = argparse.ArgumentParser(description="Index documents into ChromaDB.")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory containing sectors (subdirs) or flat files (default: data/)",
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

    # Detect sector subdirectories. A "sector" is any direct subdirectory
    # of data_dir that contains files (recursively).
    subdirs = sorted([d for d in data_dir.iterdir() if d.is_dir()])

    totals = (0, 0, 0, 0)  # n_files, n_embedded, n_skipped, n_orphans

    if subdirs:
        print(f"Detected {len(subdirs)} sectors: {[d.name for d in subdirs]}")
        for sector_dir in subdirs:
            r = ingest_sector(sector_dir, sector_dir.name, args.persist_dir)
            totals = tuple(a + b for a, b in zip(totals, r))
    else:
        # Flat mode: data_dir contains files directly, no subdirs.
        print("No subdirectories detected, falling back to flat mode "
              "(collection 'documents').")
        r = ingest_sector(data_dir, "documents", args.persist_dir)
        totals = r

    elapsed = time.time() - start
    n_files, n_embedded, n_skipped, n_orphans = totals
    print(
        f"\n=========================="
        f"\nGlobal summary"
        f"\n=========================="
        f"\nFiles indexed       : {n_files}"
        f"\nChunks embedded     : {n_embedded}"
        f"\nChunks skipped      : {n_skipped} (unchanged hash)"
        f"\nOrphans removed     : {n_orphans}"
        f"\nElapsed             : {elapsed:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
