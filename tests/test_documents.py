import re

from pcbrag import documents
from pcbrag.config import ROOT


def test_loads_all_sample_docs():
    chunks = documents.load_all(ROOT / "data")
    sources = {c.source for c in chunks}
    assert "AX3318_datasheet.md" in sources
    assert "BK1210_datasheet.pdf" in sources
    assert sum(c.doc_type == "test_log" for c in chunks) == 40


def test_ids_are_unique_and_azure_safe():
    chunks = documents.load_all(ROOT / "data")
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[A-Za-z0-9_\-=]+", i) for i in ids)


def test_pdf_chunks_have_page_numbers():
    chunks = documents.load_pdf(ROOT / "data" / "datasheets" / "BK1210_datasheet.pdf")
    assert {c.page for c in chunks} == {1, 2, 3, 4, 5}


def test_split_long_text_keeps_everything():
    text = "\n\n".join(f"paragraph {i} " + "x" * 300 for i in range(10))
    pieces = documents.split_text(text, max_chars=1000, overlap=100)
    assert len(pieces) > 1
    assert all(len(p) <= 1000 for p in pieces)
    assert "paragraph 9" in pieces[-1]
