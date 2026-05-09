from pathlib import Path

from tools.slides import chunks_to_context, parse_slides, retrieve_relevant_chunks


def test_parse_sample_pdf():
    chunks = parse_slides(Path("examples/sample_slides.pdf"))
    assert len(chunks) >= 4
    joined = " ".join(chunk.text for chunk in chunks)
    assert "Self-attention" in joined or "self-attention" in joined


def test_chunks_to_context_has_references():
    chunks = parse_slides(Path("examples/sample_slides.pdf"))
    context = chunks_to_context(chunks)
    assert "[Slide 1]" in context
    assert "[Slide 2]" in context


def test_retriever_returns_relevant_chunk():
    chunks = parse_slides(Path("examples/sample_slides.pdf"))
    results = retrieve_relevant_chunks(chunks, "self attention query key value", k=2)
    assert results
    assert any("attention" in chunk.text.lower() for chunk in results)
