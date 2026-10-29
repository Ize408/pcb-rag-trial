from pcbrag import evaluate
from pcbrag.local_index import LocalIndex, expand_query, tokenize


def test_tokenizer_keeps_part_numbers():
    toks = tokenize("Board CB-24-00117 failed rail_1v2 at 1.153 V")
    assert "cb-24-00117" in toks
    assert "1v2" in toks
    assert "1.153" in toks


def test_abbreviations_expand():
    assert "maximum" in expand_query("max input voltage")


def test_index_roundtrip(settings):
    idx = LocalIndex.load(settings.index_dir)
    hits = idx.search("absolute maximum ratings AX3318", k=1)
    assert hits[0][0].source == "AX3318_datasheet.md"


def test_eval_doesnt_regress(settings):
    for name in ("questions", "questions_hard"):
        r = evaluate.run(settings, k=5, verbose=False, name=name)
        assert r["hit@5"] >= 0.9, name
