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


def test_chunk_has_hash():
    """Each chunk carries a non-empty hash field."""
    docs = [{"source": "a.txt", "page": None, "text": "Hello world"}]

    chunks = chunk_documents(docs)

    assert "hash" in chunks[0]
    assert isinstance(chunks[0]["hash"], str)
    assert len(chunks[0]["hash"]) == 16


def test_identical_text_produces_identical_hash():
    """Two chunks with the exact same text must have the exact same hash."""
    docs = [
        {"source": "a.txt", "page": None, "text": "Hello"},
        {"source": "b.txt", "page": None, "text": "Hello"},
    ]

    chunks = chunk_documents(docs)

    assert chunks[0]["hash"] == chunks[1]["hash"]


def test_different_text_produces_different_hash():
    """A 1-character difference must change the hash."""
    docs = [
        {"source": "a.txt", "page": None, "text": "Hello"},
        {"source": "b.txt", "page": None, "text": "Hellp"},
    ]

    chunks = chunk_documents(docs)

    assert chunks[0]["hash"] != chunks[1]["hash"]


def test_section_title_detection_simple():
    """A chunk containing 'Section N - Title' should capture the title."""
    text = "Section 1 - Introduction au RAG\n" + ("X" * 200)
    docs = [{"source": "a.txt", "page": None, "text": text}]

    chunks = chunk_documents(docs, chunk_size=400, overlap=50)

    assert chunks[0]["section_title"] == "Introduction au RAG"


def test_section_title_none_before_any_header():
    """Text before any 'Section N' header should have section_title=None."""
    text = "Some intro text without any section header here."
    docs = [{"source": "a.txt", "page": None, "text": text}]

    chunks = chunk_documents(docs)

    assert chunks[0]["section_title"] is None


def test_section_title_inherited_for_mid_section_chunks():
    """A chunk starting after the header inherits the enclosing title."""
    text = (
        "Section 1 - Premier sujet\n"
        + ("a" * 1500)
        + "\nSection 2 - Deuxieme sujet\n"
        + ("b" * 1500)
    )
    docs = [{"source": "a.txt", "page": None, "text": text}]

    chunks = chunk_documents(docs, chunk_size=400, overlap=50)
    titles_seen = {c["section_title"] for c in chunks if c["section_title"]}

    assert "Premier sujet" in titles_seen
    assert "Deuxieme sujet" in titles_seen


def test_recette_title_detected():
    """'Recette N - Title' is recognized in addition to 'Section N - Title'."""
    text = "Recette 7 - Tarte aux pommes\nIngrédients..."
    docs = [{"source": "a.txt", "page": None, "text": text}]

    chunks = chunk_documents(docs)

    assert chunks[0]["section_title"] == "Tarte aux pommes"


def test_position_debut_milieu_fin():
    """Position is computed as a third of the source length."""
    # Long text with no section headers — pure position test
    text = "X" * 3000  # 3000 chars
    docs = [{"source": "a.txt", "page": None, "text": text}]

    # chunk_size=400, overlap=50, step=350 → chunks at offsets
    # 0, 350, 700, 1050, 1400, 1750, 2100, 2450, 2800
    chunks = chunk_documents(docs, chunk_size=400, overlap=50)

    positions = [c["position"] for c in chunks]
    # Lower third (offset < 1000): "début"
    # Middle third (1000 <= offset < 2000): "milieu"
    # Upper third (offset >= 2000): "fin"
    assert positions[0] == "début"
    assert "milieu" in positions
    assert positions[-1] == "fin"


def test_position_debut_for_short_doc():
    """A short doc (single chunk) is always 'début' (offset 0 / N)."""
    docs = [{"source": "a.txt", "page": None, "text": "short"}]
    chunks = chunk_documents(docs)

    assert chunks[0]["position"] == "début"
