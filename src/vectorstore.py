"""Thin wrapper around ChromaDB for the RAG pipeline.

Encapsulates the only operations we need:
    - add_chunks: store chunks with their precomputed embeddings
    - search:     find the top-k chunks closest to a query embedding
    - count:      number of chunks in the collection
    - delete:     remove chunks by id
    - get_existing_hashes: introspection used by ingest for incremental updates

The wrapper exists so we can swap ChromaDB for another vector DB later
(Qdrant, sqlite-vec, etc.) without touching the rest of the codebase.

Each VectorStore instance is bound to ONE collection. Collections act as
isolated namespaces ("sectors" in the product vocabulary): a search in
collection "medical" never sees vectors from collection "comptabilite".
Use `list_collection_names(persist_dir)` to discover what collections
exist on disk without instantiating a VectorStore for each.
"""
from pathlib import Path

import chromadb


DEFAULT_COLLECTION_NAME = "documents"


class VectorStore:
    """Wrapper for one ChromaDB collection.

    Args:
        persist_dir: directory where ChromaDB stores its files on disk.
        collection_name: name of the collection (= sector name in our model).
            Defaults to "documents" for backward compatibility with single-
            sector setups.
    """

    def __init__(
        self,
        persist_dir: str | Path = "chroma_db",
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        self.persist_dir = str(persist_dir)
        self.collection_name = collection_name
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name
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
                # Empty string sentinel for missing section title
                "section_title": c.get("section_title") or "",
                "position": c.get("position", "début"),
                # Hash stored so re-ingest can skip unchanged chunks
                "hash": c.get("hash", ""),
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

        Each result is a dict: {chunk_id, source, page, position,
        section_title, text, distance}. Sorted from most relevant
        (smallest distance) to least.
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
            section_title = meta.get("section_title") or None
            out.append({
                "chunk_id": result["ids"][0][i],
                "source": meta["source"],
                "page": page,
                "position": meta.get("position", "début"),
                "section_title": section_title,
                "text": result["documents"][0][i],
                "distance": result["distances"][0][i],
            })
        return out

    def count(self) -> int:
        """Total number of chunks currently stored in this collection."""
        return self.collection.count()

    def get_existing_hashes(self) -> dict[str, str]:
        """Return {chunk_id: hash} for every chunk in this collection."""
        if self.collection.count() == 0:
            return {}
        result = self.collection.get(include=["metadatas"])
        return {
            chunk_id: (meta.get("hash") or "")
            for chunk_id, meta in zip(result["ids"], result["metadatas"])
        }

    def delete(self, ids: list[str]) -> None:
        """Remove chunks by id. No-op if `ids` is empty."""
        if not ids:
            return
        self.collection.delete(ids=ids)


def list_collection_names(persist_dir: str | Path = "chroma_db") -> list[str]:
    """Return the names of all collections currently on disk.

    Used by ask.py to discover available sectors at startup without
    instantiating a VectorStore per collection. Returns an empty list
    if the persist_dir does not exist yet (no ingest has run).
    """
    if not Path(persist_dir).exists():
        return []
    client = chromadb.PersistentClient(path=str(persist_dir))
    return sorted(c.name for c in client.list_collections())
