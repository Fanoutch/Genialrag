"""Read PDF and TXT files from a directory into a uniform document format.

A document is a dict with keys:
    - source: str   (path to the file)
    - page:   int | None  (page number for PDFs and multi-page TXT, None otherwise)
    - text:   str   (raw text content)

For TXT files, page breaks are detected via the form feed character (U+000C),
which is the standard separator used by Word/LibreOffice when exporting to
plain text. If no form feed is present, the TXT file is treated as a single
page-less document (page=None).
"""
from pathlib import Path

from pypdf import PdfReader


FORM_FEED = "\f"  # U+000C, standard plain-text page break


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
        return [{
            "source": str(path),
            "page": None,
            "text": text,
        }]

    out: list[dict] = []
    page_num = 1
    for page_text in text.split(FORM_FEED):
        # Skip pages that are empty or just whitespace (Word sometimes
        # emits a trailing form feed)
        if page_text.strip():
            out.append({
                "source": str(path),
                "page": page_num,
                "text": page_text,
            })
        page_num += 1
    return out


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
