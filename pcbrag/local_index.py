"""
Local retriever, no Azure needed. BM25 keyword search - works surprisingly ok for
datasheets since questions usually contain the exact terms (part numbers, pin names,
"dropout"). Started with tf-idf + cosine but it ranked the BK1210 inductor page 7th
for "what inductor should I use", BM25 handles rare words like that better.
"""
import re

import joblib
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from pcbrag.documents import Chunk

TOKEN = re.compile(r"[a-z0-9]+(?:[.\-_/][a-z0-9]+)*")
STOP = set("the a an of to and or is are what which for in on at by with be do does i my it this "
           "that how much many can should from as use need get will there when why who if".split())


# people type the short forms, datasheets use the long ones. only applied to queries
ABBREV = {
    "max": "maximum", "min": "minimum", "typ": "typical", "temp": "temperature",
    "cap": "capacitor", "caps": "capacitor", "decoupling": "capacitor", "res": "resistor",
    "ldo": "low-dropout regulator ax3318", "buck": "step-down converter bk1210",
    "vin": "input voltage", "vout": "output voltage", "iq": "quiescent current",
    "freq": "frequency", "fsw": "switching frequency", "esr": "esr capacitor",
    "pinout": "pin configuration", "footprint": "package",
}


def expand_query(q):
    words = q.lower().split()
    extra = [ABBREV[w.strip("?,.")] for w in words if w.strip("?,.") in ABBREV]
    return q + (" " + " ".join(extra) if extra else "")


def tokenize(text):
    """keeps things like 3v3, cb-24-00117, rail_1v2, 6.5 together and also adds the parts
    (so "1v2" matches "rail_1v2")"""
    out = []
    for tok in TOKEN.findall(text.lower()):
        if tok in STOP:
            continue
        out.append(tok)
        parts = re.split(r"[-_/]", tok)
        if len(parts) > 1:
            out += [p for p in parts if p and p not in STOP]
    return out


class LocalIndex:
    def __init__(self, chunks=None, k1=1.5, b=0.75):
        self.chunks = chunks or []
        self.k1, self.b = k1, b
        self.vec = None
        self.matrix = None
        self.idf = None
        self.doc_len = None

    def build(self, chunks):
        self.chunks = chunks
        self.vec = CountVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None)
        self.matrix = self.vec.fit_transform([c.text for c in chunks]).tocsc().astype(np.float32)
        n = len(chunks)
        df = np.diff(self.matrix.indptr)  # docs per term
        self.idf = np.log(1 + (n - df + 0.5) / (df + 0.5))
        self.doc_len = np.asarray(self.matrix.sum(axis=1)).ravel()
        return self

    def scores(self, query):
        vocab = self.vec.vocabulary_
        terms = {vocab[t] for t in tokenize(query) if t in vocab}
        norm = self.k1 * (1 - self.b + self.b * self.doc_len / self.doc_len.mean())
        scores = np.zeros(len(self.chunks))
        for t in terms:
            col = self.matrix[:, t]
            rows, tf = col.indices, col.data
            scores[rows] += self.idf[t] * tf * (self.k1 + 1) / (tf + norm[rows])
        return scores

    def search(self, query, k=5, doc_type=None):
        scores = self.scores(expand_query(query))
        order = scores.argsort()[::-1]
        hits = []
        for i in order:
            if scores[i] <= 0:
                break
            if doc_type and self.chunks[i].doc_type != doc_type:
                continue
            hits.append((self.chunks[i], float(scores[i])))
            if len(hits) == k:
                break
        return hits

    def save(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        joblib.dump({"chunks": [c.to_dict() for c in self.chunks], "vec": self.vec,
                     "matrix": self.matrix, "idf": self.idf, "doc_len": self.doc_len},
                    folder / "local.joblib")

    @classmethod
    def load(cls, folder):
        d = joblib.load(folder / "local.joblib")
        idx = cls([Chunk(**c) for c in d["chunks"]])
        idx.vec, idx.matrix, idx.idf, idx.doc_len = d["vec"], d["matrix"], d["idf"], d["doc_len"]
        return idx
