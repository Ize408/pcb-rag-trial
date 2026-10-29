"""azure code paths with fake clients, no network"""
from types import SimpleNamespace

from pcbrag.azure_index import AzureIndex, build_index_definition
from pcbrag.config import Settings
from pcbrag.documents import Chunk


class FakeOpenAI:
    def __init__(self, dim=8):
        self.dim = dim
        self.embeddings = SimpleNamespace(create=self.create)

    def create(self, model, input):
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1] * self.dim) for _ in input])


class FakeSearch:
    def __init__(self):
        self.uploaded, self.queries = [], []

    def merge_or_upload_documents(self, documents):
        self.uploaded += documents
        return [SimpleNamespace(key=d["id"], succeeded=True) for d in documents]

    def search(self, **kw):
        self.queries.append(kw)
        return [{"id": "a", "text": "VIN to GND 6.5 V", "source": "AX3318_datasheet.md",
                 "doc_type": "datasheet", "title": "AX3318", "section": "3 Absolute", "page": None,
                 "@search.score": 0.03}]


class FakeAdmin:
    def __init__(self):
        self.created = []

    def create_or_update_index(self, index):
        self.created.append(index)

    def delete_index(self, name):
        pass


def make(dim=8):
    s = Settings(embed_dim=dim)
    return AzureIndex(s, openai=FakeOpenAI(dim), search=FakeSearch(), index_admin=FakeAdmin())


def test_index_definition():
    d = build_index_definition("pcb-docs", 1536).as_dict()
    emb = [f for f in d["fields"] if f["name"] == "embedding"][0]
    assert emb["dimensions"] == 1536
    assert [f for f in d["fields"] if f.get("key")][0]["name"] == "id"


def test_build_uploads_with_embeddings():
    idx = make()
    chunks = [Chunk(f"id{i}", f"text {i}", "x.md", "datasheet") for i in range(150)]
    idx.build(chunks)
    assert len(idx.search_client.uploaded) == 150
    assert len(idx.search_client.uploaded[0]["embedding"]) == 8
    assert idx.index_admin.created


def test_search_is_hybrid():
    idx = make()
    hits = idx.search("max input voltage", k=3, doc_type="datasheet")
    q = idx.search_client.queries[0]
    assert q["search_text"] == "max input voltage"
    assert q["vector_queries"][0].fields == "embedding"
    assert q["filter"] == "doc_type eq 'datasheet'"
    assert hits[0][0].source == "AX3318_datasheet.md"
    assert hits[0][0].page == 0
