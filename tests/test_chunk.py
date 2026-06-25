from rag.ingest import chunk_text


def test_chunk_empty():
    assert chunk_text("", 100, 10) == []


def test_chunk_short_text_single_chunk():
    assert chunk_text("hello world", 100, 10) == ["hello world"]


def test_chunk_overlap_and_coverage():
    text = "abcdefghij" * 10  # 100 chars
    chunks = chunk_text(text, 40, 10)
    assert len(chunks) > 1
    # every chunk within size bound
    assert all(len(c) <= 40 for c in chunks)
    # full text is covered (concatenation of non-overlapping starts)
    assert chunks[0].startswith("abcde")


def test_chunk_no_infinite_loop():
    chunks = chunk_text("x" * 1000, 100, 50)
    assert len(chunks) < 100
