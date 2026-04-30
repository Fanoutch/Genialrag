"""RAG orchestration: question → retrieval → prompt → generation."""
from pathlib import Path

from src.llm_client import embed_texts, generate
from src.vectorstore import VectorStore


PROMPT_TEMPLATE = """Tu es un assistant qui répond à des questions en te basant UNIQUEMENT sur le contenu des extraits ci-dessous.

Procédure à suivre :
1. Lis le CONTENU (le texte sous chaque entête) de chaque extrait.
2. Si la réponse à la question se trouve dans ce contenu, formule une réponse complète en t'appuyant sur le texte (paraphrase ou citation directe).
3. Si la réponse n'est dans aucun extrait, réponds simplement "Je ne sais pas".
4. À la fin de ta réponse, ajoute la citation entre crochets : [source: <étiquette>] où <étiquette> est la chaîne qui apparaît après "source:" dans l'extrait que tu as utilisé.

Important : l'étiquette de la source sert UNIQUEMENT à indiquer d'où vient l'information ; elle ne remplace JAMAIS la réponse elle-même. Tu dois toujours écrire d'abord une vraie phrase de réponse avant la citation.

Exemple de réponse correcte :
La capitale de la France est Paris. [source: geographie.txt (début) - Capitales européennes]

EXTRAITS :
{extraits}

QUESTION : {question}

RÉPONSE :"""


SNIPPET_MAX_CHARS = 80


def _make_snippet(text: str, max_chars: int = SNIPPET_MAX_CHARS) -> str:
    """Return the first non-empty line of `text`, truncated to max_chars.

    Used as a fallback "label" for chunks that have no detected section title.
    The user can copy-paste this snippet into Ctrl+F to find the exact passage.
    """
    for line in text.splitlines():
        line = line.strip()
        if line:
            if len(line) > max_chars:
                return line[:max_chars].rstrip() + "..."
            return line
    return ""


def _format_location(chunk: dict) -> str:
    """Compose the spatial-location part of the citation.

    Examples:
        "page 3, milieu"   for a PDF chunk in the middle of page 3
        "début"             for a TXT chunk at the start of the document
    """
    pos = chunk.get("position", "début")
    page = chunk.get("page")
    if page is not None:
        return f"page {page}, {pos}"
    return pos


def _format_label(chunk: dict) -> str:
    """Compose the descriptive part of the citation.

    Returns the section title if detected, otherwise a snippet of the chunk.
    """
    title = chunk.get("section_title")
    if title:
        return title
    return _make_snippet(chunk.get("text", ""))


def _format_citation(chunk: dict) -> str:
    """Build the full citation label for a chunk.

    Format: "filename (location) — label"
    """
    name = Path(chunk["source"]).name
    location = _format_location(chunk)
    label = _format_label(chunk)
    base = f"{name} ({location})"
    if label:
        return f"{base} — {label}"
    return base


def build_prompt(question: str, chunks: list[dict]) -> str:
    """Assemble the final prompt sent to the LLM."""
    if chunks:
        parts = []
        for i, c in enumerate(chunks, start=1):
            citation = _format_citation(c)
            header = f"[Extrait {i} — source: {citation}]"
            parts.append(f"---\n{header}\n{c['text']}")
        extraits = "\n".join(parts) + "\n---"
    else:
        extraits = "(aucun extrait disponible)"

    return PROMPT_TEMPLATE.format(extraits=extraits, question=question)


def format_sources(chunks: list[dict]) -> str:
    """Format the list of sources for display under the answer.

    Deduplicates lines that produce the exact same citation string so the
    same passage isn't listed twice.
    """
    if not chunks:
        return "Sources : aucune"

    seen: set[str] = set()
    lines = ["Sources :"]
    for c in chunks:
        citation = _format_citation(c)
        if citation in seen:
            continue
        seen.add(citation)
        lines.append(f"  - {citation}")
    return "\n".join(lines)


def answer_question(
    question: str,
    vectorstore: VectorStore,
    top_k: int = 6,
) -> dict:
    """Run the full RAG pipeline for a single question.

    Default top_k=6 is calibrated for the semantic chunker (sections
    average ~400-500 chars, so 6 chunks ≈ 3000 chars of context — similar
    to what 4 fixed-size 800-char chunks gave previously).

    Returns: {"answer": str, "sources": list[dict]}
    """
    query_vec = embed_texts([question])[0]
    chunks = vectorstore.search(query_vec, top_k=top_k)
    prompt = build_prompt(question, chunks)
    answer = generate(prompt)
    return {"answer": answer, "sources": chunks}
