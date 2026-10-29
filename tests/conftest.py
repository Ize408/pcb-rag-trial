import pytest

from pcbrag import documents
from pcbrag.config import ROOT, Settings
from pcbrag.local_index import LocalIndex


@pytest.fixture(scope="session")
def settings(tmp_path_factory):
    s = Settings(index_dir=tmp_path_factory.mktemp("index"), retriever="local")
    s.aoai_endpoint = s.aoai_key = ""  # tests never call azure for real
    LocalIndex().build(documents.load_all(ROOT / "data")).save(s.index_dir)
    return s
