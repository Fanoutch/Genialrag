"""Read PDF and TXT files from a directory into a uniform document format.

A document is a dict with keys:
    - source: str   (path to the file)
    - page:   int | None  (page number for PDFs and multi-page TXT, None otherwise)
    - text:   str   (raw text content, with administrative boilerplate stripped)

For TXT files, page breaks are detected via the form feed character (U+000C),
which is the standard separator used by Word/LibreOffice when exporting to
plain text. If no form feed is present, the TXT file is treated as a single
page-less document (page=None).

Extracted text goes through a light cleanup step (`_clean_text`) that removes
common page-header / page-footer boilerplate (lone page numbers, "X/Y" prefixes
stuck to content, military admin lines like "BCRM ..."). The goal is to keep
real content while stripping noise that pollutes embeddings.
"""
import re
from pathlib import Path

from pypdf import PdfReader


FORM_FEED = "\f"  # U+000C, standard plain-text page break

# --- Cleanup patterns (applied in order) ---

# A whole line that is just a page indicator like "5/10" (with optional
# whitespace).
LONE_PAGE_NUMBER_LINE = re.compile(r"^\s*\d+\s*/\s*\d+\s*$", re.MULTILINE)

# Same indicator stuck at the START of a line, BEFORE actual content.
# Example: "5/10 2. UTILISATION DES MARGES ..." → strip "5/10 ".
PAGE_NUMBER_PREFIX = re.compile(r"^\s*\d+\s*/\s*\d+\s+", re.MULTILINE)

# Common admin header lines from the maintenance corpus (Marine nationale).
# These are 100% metadata, never useful semantically.
ADMIN_LINE_PATTERNS = [
    re.compile(r"^.*BCRM de .*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*BP \d+\s*[–-].*$", re.MULTILINE),
    re.compile(r"^\s*\S+@intradef\.gouv\.fr\s*$", re.MULTILINE),
    re.compile(r"^\s*Dossier suivi par\s*:.*$", re.MULTILINE | re.IGNORECASE),
]

# Collapse runs of 3+ blank lines into 2 (preserves paragraph boundaries).
EXCESSIVE_BLANK_LINES = re.compile(r"\n\s*\n\s*\n+")


def _clean_text(text: str) -> str:
    """Remove common page-level boilerplate from extracted text.

    Order matters:
    1. Strip page-number prefixes that are stuck to the start of a line
       (so subsequent line-start regexes can match the real content).
    2. Strip lone page-number lines.
    3. Strip admin metadata lines.
    4. Collapse the resulting blank-line runs.
    """
    text = PAGE_NUMBER_PREFIX.sub("", text)
    text = LONE_PAGE_NUMBER_LINE.sub("", text)
    for pattern in ADMIN_LINE_PATTERNS:
        text = pattern.sub("", text)
    text = EXCESSIVE_BLANK_LINES.sub("\n\n", text)
    return text


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
            docs.extend(_load_txt(path))
        elif suffix == ".pdf":
            docs.extend(_load_pdf(path))

    return docs


def _load_txt(path: Path) -> list[dict]:
    """Read a TXT file, splitting on form-feed characters if present.

    No form feed → 1 entry with page=None (current behavior).
    Form feeds present → 1 entry per page with page=1, 2, 3, ...
    """
    text = path.read_text(encoding="utf-8")

    if FORM_FEED not in text:
        cleaned = _clean_text(text)
        return [{
            "source": str(path),
            "page": None,
            "text": cleaned,
        }]

    out: list[dict] = []
    page_num = 1
    for page_text in text.split(FORM_FEED):
        cleaned = _clean_text(page_text)
        # Skip pages that are empty or just whitespace (Word sometimes
        # emits a trailing form feed)
        if cleaned.strip():
            out.append({
                "source": str(path),
                "page": page_num,
                "text": cleaned,
            })
        page_num += 1
    return out


def _load_pdf(path: Path) -> list[dict]:
    reader = PdfReader(str(path))
    out = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned = _clean_text(text)
        out.append({
            "source": str(path),
            "page": i,
            "text": cleaned,
        })
    return out
