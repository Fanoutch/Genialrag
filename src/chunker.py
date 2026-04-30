"""Split documents into overlapping fixed-size chunks.

A chunk is a dict with keys:
    - chunk_id:      str         unique stable id (e.g. "manuel.pdf_p3_c0")
    - source:        str         path to the source file
    - page:          int | None  page number when known
    - position:      str         one of "début", "milieu", "fin" — relative
                                 location of the chunk inside its source
                                 (page for PDFs / multi-page TXT, document
                                 for single-page TXT)
    - section_title: str | None  full title of the enclosing "Section N - ..."
                                 or "Recette N - ..." if detected, else None
    - text:          str         raw chunk text
    - hash:          str         sha256 of text (truncated to 16 hex chars),
                                 used to detect content changes between runs
"""
import hashlib
import re


# Captures the full title after "Section N -" / "Recette N -".
# - Group 1 = the title text (everything after the dash up to end of line).
# - Allowed separators between number and title: em-dash, hyphen, colon,
#   or just whitespace.
SECTION_HEADER_PATTERN = re.compile(
    r"\b(?:Section|Recette)\s+\d+\s*[—\-:]?\s*([^\n]+)",
    re.IGNORECASE,
)


def _hash_text(text: str) -> str:
    """Return a short, stable, content-addressed fingerprint of `text`.

    Uses SHA-256 truncated to 16 hex chars. Plenty unique for our needs
    (collision risk negligible at this scale) and short enough to keep
    metadata lightweight.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _parse_section_headers(text: str) -> list[tuple[int, str]]:
    """Find all 'Section N - Title' / 'Recette N - Title' headers in `text`.

    Returns a list of (offset, title) tuples sorted by offset.
    The title is stripped of surrounding whitespace.
    """
    return [
        (m.start(), m.group(1).strip())
        for m in SECTION_HEADER_PATTERN.finditer(text)
    ]


def _section_title_at_offset(
    headers: list[tuple[int, str]],
    offset: int,
) -> str | None:
    """Return the section title that contains the chunk starting at `offset`.

    Strategy: the section is the most recent header at or before `offset`.
    Returns None if `offset` is before the first header.
    """
    current: str | None = None
    for header_offset, title in headers:
        if header_offset <= offset:
            current = title
        else:
            break
    return current


def _position_at_offset(offset: int, total_length: int) -> str:
    """Return 'début', 'milieu' or 'fin' based on the chunk's relative offset.

    - début : first third of the source
    - milieu: middle third
    - fin   : last third
    Empty docs default to 'début'.
    """
    if total_length <= 0:
        return "début"
    ratio = offset / total_length
    if ratio < 1 / 3:
        return "début"
    if ratio < 2 / 3:
        return "milieu"
    return "fin"


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

    # Pre-parse section titles once per document so we can assign each
    # chunk to its enclosing section even when the chunk starts mid-section
    # (because of the overlap).
    headers = _parse_section_headers(text)
    total_length = len(text)

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
            "position": _position_at_offset(i, total_length),
            "section_title": _section_title_at_offset(headers, i),
            "text": piece,
            "hash": _hash_text(piece),
        })
        chunk_index += 1
        if i + chunk_size >= len(text):
            break
        i += step
    return out
