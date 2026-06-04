from agents.lambdas.reembed.chunker import chunk_markdown

DOC = """# Title

Intro paragraph about AI maturity.

## Stage 1

Stage one means ad hoc experimentation.

## Stage 2

Stage two means piloting with intent.

### Stage 2 details

More on piloting.
"""


def test_basic_heading_paths():
    # Small budget keeps sections in their own chunks so the nested path surfaces.
    chunks = chunk_markdown(DOC, max_tokens=12, overlap_tokens=2, chars_per_token=4)
    assert chunks, "should produce at least one chunk"
    # Heading hierarchy is tracked; the deepest section nests under its parents.
    paths = [c.heading_path for c in chunks]
    assert ["Title", "Stage 2", "Stage 2 details"] in paths


def test_indices_are_sequential():
    chunks = chunk_markdown(DOC)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_small_doc_packs_into_one_chunk():
    chunks = chunk_markdown(DOC, max_tokens=1000)
    assert len(chunks) == 1
    assert "Stage 2 details" in chunks[0].text


def test_long_section_splits_with_overlap():
    body = " ".join(f"word{i}" for i in range(2000))
    md = f"# Big\n\n{body}\n"
    chunks = chunk_markdown(md, max_tokens=100, overlap_tokens=10, chars_per_token=4)
    assert len(chunks) > 1
    # Consecutive chunks share overlap: the tail of one appears in the next.
    first_tail = chunks[0].text.split()[-1]
    assert first_tail in chunks[1].text
    for c in chunks:
        assert c.heading_path == ["Big"]


def test_empty_document_yields_no_chunks():
    assert chunk_markdown("   \n\n  ") == []
