from types import SimpleNamespace

from pcbrag.assistant import SYSTEM_PROMPT, Assistant


class FakeLLM:
    """records what we send to azure openai"""

    def __init__(self):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls.append(kw)
        msg = SimpleNamespace(content="VIN abs max is 6.5 V [1]")
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_prompt_has_numbered_context(settings):
    llm = FakeLLM()
    ans = Assistant(settings, llm=llm).ask("absolute max input voltage AX3318")
    assert ans.used_llm and "6.5" in ans.text
    msgs = llm.calls[0]["messages"]
    assert msgs[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert "[1] AX3318_datasheet.md" in msgs[-1]["content"]
    assert llm.calls[0]["temperature"] <= 0.2


def test_history_is_sent(settings):
    llm = FakeLLM()
    Assistant(settings, llm=llm).ask("and the output?", history=[("q1", "a1")])
    roles = [m["role"] for m in llm.calls[0]["messages"]]
    assert roles == ["system", "user", "assistant", "user"]


def test_counting_questions_get_stats(settings):
    chunks = Assistant(settings).retrieve("which test step fails most often?")
    assert chunks[0].doc_type == "stats"
    assert "uart_loopback: 4" in chunks[0].text


def test_no_llm_falls_back_to_passages(settings):
    ans = Assistant(settings).ask("BK1210 inductor")
    assert not ans.used_llm
    assert "2.2 uH" in ans.text
