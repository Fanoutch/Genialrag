"""Tests for the RAG orchestration helpers."""
from src.rag import build_prompt, format_sources


def _chunk(source, text, page=None, section_title=None, position="début"):
    """Helper to build a chunk dict with the new fields."""
    return {
        "source": source,
        "text": text,
        "page": page,
        "section_title": section_title,
        "position": position,
    }


def test_build_prompt_includes_question():
    chunks = [_chunk("manuel.pdf", "Le RAG fonctionne ainsi.", page=3,
                     section_title="Introduction", position="début")]
    prompt = build_prompt("Comment fonctionne le RAG ?", chunks)

    assert "Comment fonctionne le RAG ?" in prompt
    assert "Le RAG fonctionne ainsi." in prompt


def test_build_prompt_includes_all_chunks_with_sources():
    chunks = [
        _chunk("a.pdf", "Premier extrait.", page=1, section_title="Intro"),
        _chunk("b.txt", "Second extrait.", section_title="Conclusion",
               position="fin"),
    ]
    prompt = build_prompt("Une question ?", chunks)

    assert "Premier extrait." in prompt
    assert "Second extrait." in prompt
    assert "a.pdf" in prompt
    assert "b.txt" in prompt
    assert "page 1" in prompt
    assert "Intro" in prompt
    assert "Conclusion" in prompt


def test_build_prompt_instructs_to_say_idk():
    """The prompt must tell the model to say 'Je ne sais pas' if no answer."""
    prompt = build_prompt("Q ?", [])

    assert "Je ne sais pas" in prompt


def test_format_sources_uses_section_title_when_available():
    chunks = [
        _chunk("data/manuel.pdf", "...", page=3, section_title="Entretien",
               position="milieu"),
    ]

    formatted = format_sources(chunks)

    assert "manuel.pdf (page 3, milieu) — Entretien" in formatted


def test_format_sources_falls_back_to_snippet_when_no_title():
    """Without section_title, the first line of the chunk is used as label."""
    chunks = [
        _chunk("data/notes.txt", "Premier paragraphe important du fichier.\nReste...",
               position="début"),
    ]

    formatted = format_sources(chunks)

    assert "notes.txt (début) — Premier paragraphe important du fichier." in formatted


def test_format_sources_dedupes_identical_citations():
    """Two chunks producing the exact same citation string appear once."""
    chunks = [
        _chunk("a.txt", "...", section_title="Sujet X", position="début"),
        _chunk("a.txt", "...", section_title="Sujet X", position="début"),
    ]

    formatted = format_sources(chunks)

    # The "Sujet X" line should appear only once
    assert formatted.count("Sujet X") == 1


def test_format_sources_keeps_distinct_sections():
    """Two chunks with different section titles both appear."""
    chunks = [
        _chunk("a.txt", "...", section_title="Sujet A", position="début"),
        _chunk("a.txt", "...", section_title="Sujet B", position="milieu"),
    ]

    formatted = format_sources(chunks)

    assert "Sujet A" in formatted
    assert "Sujet B" in formatted


def test_format_sources_empty():
    assert format_sources([]) == "Sources : aucune"
