from fastapi.testclient import TestClient

import pcbrag.server as server
from pcbrag.assistant import Assistant


def test_ask_endpoint(settings):
    server._bot = Assistant(settings)
    c = TestClient(server.app)
    assert c.get("/api/health").json()["retriever"] == "local"
    r = c.post("/api/ask", json={"question": "Which test point is the 3V3 rail?"}).json()
    assert r["sources"][0]["n"] == 1
    assert "TP1" in r["answer"]
    assert "<html" in c.get("/").text
