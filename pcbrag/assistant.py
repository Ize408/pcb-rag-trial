import re
from dataclasses import dataclass, field

from pcbrag import testlogs
from pcbrag.config import Settings
from pcbrag.documents import Chunk

SYSTEM_PROMPT = """You are a hardware engineering assistant. You answer questions about PCB \
component datasheets, board specifications and production test logs.

Rules:
- Only use the numbered context below. Cite every fact like [1] or [2][3].
- Keep units and conditions with every number (e.g. "180 mV typ at 300 mA").
- Be careful with limits: absolute maximum ratings are NOT operating conditions. Say which one you mean.
- If the context doesn't contain the answer, say you couldn't find it in the documents. \
Never guess electrical values, a wrong limit can damage hardware.
- Keep it short. Use a small table only if comparing several values."""

# questions that need counting over all logs instead of a few retrieved ones
AGGREGATE = re.compile(r"\b(how many|which boards|most common|most often|yield|failure rate|"
                       r"fail(ed|ing|ures)? (the )?most|all boards|per lot|by lot|trend|summary)\b", re.I)


@dataclass
class Answer:
    text: str
    sources: list = field(default_factory=list)
    used_llm: bool = False


def load_index(settings):
    if settings.retriever == "azure":
        from pcbrag.azure_index import AzureIndex
        return AzureIndex(settings)
    from pcbrag.local_index import LocalIndex
    path = settings.index_dir
    if not (path / "local.joblib").exists():
        raise SystemExit("no local index yet, run: python -m pcbrag ingest")
    return LocalIndex.load(path)


class Assistant:
    def __init__(self, settings=None, index=None, llm=None):
        self.s = settings or Settings()
        self.index = index or load_index(self.s)
        self.llm = llm
        if self.llm is None and self.s.llm_enabled:
            from pcbrag.azure_index import openai_client
            self.llm = openai_client(self.s)
        self._log_stats = None

    def log_stats(self):
        if self._log_stats is None:
            self._log_stats = testlogs.stats(testlogs.parse_dir(self.s.data_dir / "test_logs"))
        return self._log_stats

    def retrieve(self, question, k=None):
        k = k or self.s.top_k
        hits = [c for c, _ in self.index.search(question, k=k)]
        if AGGREGATE.search(question):
            stats = Chunk("stats", self.log_stats(), "test log statistics (all logs)", "stats",
                          "Test log statistics")
            hits = [stats] + hits[:k - 1]
        return hits

    @staticmethod
    def build_context(chunks):
        return "\n\n".join(f"[{i}] {c.header()}\n{c.text}" for i, c in enumerate(chunks, 1))

    def ask(self, question, k=None, history=None):
        chunks = self.retrieve(question, k)
        if not chunks:
            return Answer("I couldn't find anything about that in the documents.")
        if self.llm is None:
            return Answer(self.extractive(question, chunks), chunks, False)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for q, a in (history or [])[-3:]:  # a bit of chat memory for follow ups
            messages += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
        messages.append({"role": "user", "content":
                         f"Context:\n{self.build_context(chunks)}\n\nQuestion: {question}"})
        resp = self.llm.chat.completions.create(model=self.s.chat_deployment, messages=messages,
                                                temperature=0.1, max_tokens=600)
        return Answer(resp.choices[0].message.content.strip(), chunks, True)

    @staticmethod
    def extractive(question, chunks, max_chars=900):
        """no LLM configured: just show the best matching passages. tried picking single
        lines first but the line with the answer often shares no words with the question
        ("VIN to GND: 6.5 V" vs "max input voltage")"""
        parts = ["(no LLM configured - here are the best matching passages)"]
        for n, c in enumerate(chunks[:2], 1):
            body = "\n".join(l for l in c.text.splitlines()
                             if not l.startswith(("Section:", "#")) and l.strip() != c.title).strip()
            if len(body) > max_chars:
                body = body[:max_chars].rsplit("\n", 1)[0] + "\n..."
            parts.append(f"[{n}] {c.header()}\n{body}")
        return "\n\n".join(parts)
