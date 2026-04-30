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


def test_txt_with_form_feed_yields_multiple_pages(tmp_path):
    """A TXT file containing form-feed chars splits into one doc per page."""
    txt = tmp_path / "report.txt"
    # Three pages separated by \f (typical of Word -> plain text export)
    txt.write_text("Page one content\fPage two content\fPage three", encoding="utf-8")

    docs = load_documents(tmp_path)

    assert len(docs) == 3
    assert [d["page"] for d in docs] == [1, 2, 3]
    assert docs[0]["text"] == "Page one content"
    assert docs[1]["text"] == "Page two content"
    assert docs[2]["text"] == "Page three"


def test_txt_without_form_feed_keeps_page_none(tmp_path):
    """A TXT file without form feed stays as a single page=None doc."""
    txt = tmp_path / "simple.txt"
    txt.write_text("Single page text content here.", encoding="utf-8")

    docs = load_documents(tmp_path)

    assert len(docs) == 1
    assert docs[0]["page"] is None


def test_txt_skips_empty_pages_between_form_feeds(tmp_path):
    """Empty pages (e.g., trailing form feed) are skipped, not numbered."""
    txt = tmp_path / "trailing.txt"
    # Last \f produces an empty trailing page
    txt.write_text("Page one\fPage two\f", encoding="utf-8")

    docs = load_documents(tmp_path)

    assert len(docs) == 2
    assert [d["page"] for d in docs] == [1, 2]


def test_clean_strips_lone_page_number_lines(tmp_path):
    """A line that is just '5/10' should be stripped from the loaded text."""
    txt = tmp_path / "doc.txt"
    txt.write_text(
        "Real content here.\n5/10\nMore real content.",
        encoding="utf-8",
    )

    docs = load_documents(tmp_path)

    assert "5/10" not in docs[0]["text"]
    assert "Real content here." in docs[0]["text"]
    assert "More real content." in docs[0]["text"]


def test_clean_strips_page_number_prefix_stuck_to_content(tmp_path):
    """'5/10 2. UTILISATION' should become '2. UTILISATION' after cleanup."""
    txt = tmp_path / "doc.txt"
    txt.write_text(
        "5/10 2. UTILISATION DES MARGES\nContenu...",
        encoding="utf-8",
    )

    docs = load_documents(tmp_path)
    text = docs[0]["text"]

    assert text.startswith("2. UTILISATION DES MARGES")
    assert "5/10" not in text


def test_clean_strips_admin_lines(tmp_path):
    """BCRM and 'Dossier suivi par' lines should be stripped."""
    txt = tmp_path / "doc.txt"
    txt.write_text(
        "BCRM de Toulon – BAN Hyères - GSTA\n"
        "BP 200 – 83800 Toulon cedex 9\n"
        "lucas.sevestre@intradef.gouv.fr\n"
        "Dossier suivi par : EV1 Sevestre\n"
        "1. PRESENTATION\n"
        "Vrai contenu du document.",
        encoding="utf-8",
    )

    docs = load_documents(tmp_path)
    text = docs[0]["text"]

    assert "BCRM" not in text
    assert "intradef" not in text
    assert "Dossier suivi par" not in text
    assert "1. PRESENTATION" in text
    assert "Vrai contenu" in text


def test_clean_preserves_real_content(tmp_path):
    """Cleanup should not destroy meaningful content (titles, sections, etc.)."""
    txt = tmp_path / "doc.txt"
    original = (
        "Titre du document\n"
        "Section 1 - Introduction\n"
        "Le contenu de cette section est important.\n"
        "1.1. Sous-section\n"
        "Avec encore du contenu utile."
    )
    txt.write_text(original, encoding="utf-8")

    docs = load_documents(tmp_path)
    text = docs[0]["text"]

    for needle in [
        "Titre du document",
        "Section 1",
        "Introduction",
        "1.1. Sous-section",
        "contenu utile",
    ]:
        assert needle in text, f"missing: {needle!r}"
