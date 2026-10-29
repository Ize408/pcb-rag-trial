"""
Small eval set. For each question we know which file has the answer and a string
that has to be in it. Checks:
  hit@k     - the right file is in the top k results
  found@k   - the expected string is somewhere in the retrieved text (what the LLM gets to see)
  answer    - (--llm) the expected string shows up in the final answer
"""
import json

from pcbrag.assistant import Assistant
from pcbrag.config import ROOT


def load_questions(name="questions"):
    path = ROOT / "eval" / f"{name}.jsonl"
    return [json.loads(line) for line in open(path) if line.strip()]


def run(settings, k=5, with_llm=False, questions=None, verbose=True, name="questions"):
    bot = Assistant(settings)
    questions = questions or load_questions(name)
    hit = found = answered = 0
    for q in questions:
        chunks = bot.retrieve(q["question"], k)
        sources = [c.source for c in chunks]
        text = " ".join(c.text for c in chunks).lower()
        h = any(q["source"] in s for s in sources)
        f = q["expect"].lower() in text
        hit += h
        found += f
        line = f"{'ok ' if h and f else 'MISS'}  {q['question'][:70]:<70}"
        if with_llm and bot.llm:
            ans = bot.ask(q["question"], k).text
            ok = q["expect"].lower() in ans.lower()
            answered += ok
            line += "  answer " + ("ok" if ok else "WRONG")
        if verbose:
            print(line)
    n = len(questions)
    result = {"questions": n, f"hit@{k}": hit / n, f"found@{k}": found / n}
    if with_llm and bot.llm:
        result["answer_acc"] = answered / n
    if verbose:
        print("\n" + "  ".join(f"{key}: {v:.0%}" if isinstance(v, float) else f"{key}: {v}"
                               for key, v in result.items()))
    return result
