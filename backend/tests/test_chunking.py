from app.services.rag.chunking import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_returns_single_chunk() -> None:
    chunks = chunk_text("Hello world.", chunk_size=800)
    assert chunks == ["Hello world."]


def test_long_text_splits_into_multiple_chunks() -> None:
    text = " ".join(f"This is sentence number {i}." for i in range(200))
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 250  # allows a little slack for the overlap prefix


def test_chunks_have_overlap() -> None:
    text = " ".join(f"Sentence {i}." for i in range(100))
    chunks = chunk_text(text, chunk_size=100, overlap=30)
    assert len(chunks) > 1
    # The tail of chunk N should reappear at the start of chunk N+1.
    tail_of_first = chunks[0][-20:]
    assert tail_of_first[-10:] in chunks[1]


def test_single_very_long_sentence_is_hard_split() -> None:
    text = "word " * 500  # one giant "sentence" (no punctuation)
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_no_content_lost_across_chunks() -> None:
    """Every word in the source text should appear somewhere in the chunks."""
    text = ". ".join(f"Fact number {i} is true" for i in range(50)) + "."
    chunks = chunk_text(text, chunk_size=150, overlap=30)
    combined = " ".join(chunks)
    for i in range(50):
        assert f"Fact number {i} is true" in combined
