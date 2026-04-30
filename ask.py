"""CLI: interactive Q&A loop over the indexed documents, scoped by sector.

At startup, the user selects a sector among the available collections.
Questions are then answered using ONLY the chunks of that sector — no
cross-domain pollution. The user can switch sector mid-session by typing
'changer' and exit by typing 'quit'.

Each question is independent (one-shot, no conversational memory).

Usage:
    python ask.py
"""
import sys
from pathlib import Path

from src.rag import answer_question, format_sources
from src.vectorstore import VectorStore, list_collection_names


PERSIST_DIR = "chroma_db"


def select_sector(sectors: list[str]) -> str | None:
    """Prompt the user to pick a sector. Returns the sector name or None to quit."""
    print("\nGenialrag — Sélection du domaine")
    print("─" * 36)
    for i, s in enumerate(sectors, 1):
        store = VectorStore(persist_dir=PERSIST_DIR, collection_name=s)
        print(f"  {i}. {s:<20} ({store.count()} chunks)")
    print()
    while True:
        try:
            raw = input("Choisis un domaine (numéro ou nom, 'quit' pour sortir) > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not raw:
            continue
        if raw.lower() in {"quit", "exit", "q"}:
            return None
        # Try as a number first
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(sectors):
                return sectors[idx - 1]
            print(f"  ✗ Numéro hors plage (1-{len(sectors)})")
            continue
        # Then as a name
        if raw in sectors:
            return raw
        # Fuzzy: case-insensitive prefix match
        candidates = [s for s in sectors if s.lower().startswith(raw.lower())]
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            print(f"  ✗ Ambigu : {candidates}")
        else:
            print(f"  ✗ Domaine inconnu")


def run_questions(store: VectorStore, sector: str) -> str:
    """Loop questions for one sector. Returns 'quit' or 'changer'."""
    print(f"\n✓ Domaine actif : {sector}")
    print("Tape 'changer' pour changer de domaine, 'quit' pour sortir.\n")

    while True:
        try:
            question = input(f"Question ({sector}) > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"

        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            return "quit"
        if question.lower() in {"changer", "change", "switch"}:
            return "changer"

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


def main() -> int:
    if not Path(PERSIST_DIR).exists():
        print(
            f"Error: vector store '{PERSIST_DIR}/' does not exist.\n"
            f"Run 'python ingest.py' first to index your documents.",
            file=sys.stderr,
        )
        return 1

    sectors = list_collection_names(PERSIST_DIR)
    if not sectors:
        print(
            "No sectors found. Run 'python ingest.py' first to index your "
            "documents into one or more sector subdirectories of data/.",
            file=sys.stderr,
        )
        return 1

    while True:
        chosen = select_sector(sectors)
        if chosen is None:
            print("Bye.")
            return 0

        store = VectorStore(persist_dir=PERSIST_DIR, collection_name=chosen)
        action = run_questions(store, chosen)
        if action == "quit":
            print("Bye.")
            return 0
        # action == "changer" → loop back to selection


if __name__ == "__main__":
    sys.exit(main())
