"""
python -m pcbrag ingest            build the index from data/
python -m pcbrag ask "question"
python -m pcbrag chat              interactive
python -m pcbrag stats             test log failure summary
python -m pcbrag eval              retrieval eval on eval/questions.jsonl
"""
import argparse
import sys

from pcbrag import documents, testlogs
from pcbrag.config import Settings


def cmd_ingest(s, args):
    chunks = documents.load_all(s.data_dir)
    print(f"loaded {len(chunks)} chunks from {s.data_dir}")
    if s.retriever == "azure":
        from pcbrag.azure_index import AzureIndex
        AzureIndex(s).build(chunks, recreate=args.recreate)
        print(f"uploaded to Azure AI Search index '{s.search_index}'")
    else:
        from pcbrag.local_index import LocalIndex
        LocalIndex().build(chunks).save(s.index_dir)
        print(f"saved local index to {s.index_dir}")


def print_answer(ans, show_sources=True):
    print("\n" + ans.text + "\n")
    if show_sources:
        for i, c in enumerate(ans.sources, 1):
            print(f"  [{i}] {c.header()}")
    print()


def cmd_ask(s, args):
    from pcbrag.assistant import Assistant
    print_answer(Assistant(s).ask(" ".join(args.question), k=args.k))


def cmd_chat(s, args):
    from pcbrag.assistant import Assistant
    bot = Assistant(s)
    history = []
    print("ask about the datasheets / test logs. empty line to quit")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        ans = bot.ask(q, history=history)
        history.append((q, ans.text))
        print_answer(ans)


def cmd_stats(s, args):
    print(testlogs.stats(testlogs.parse_dir(s.data_dir / "test_logs")))


def cmd_eval(s, args):
    from pcbrag import evaluate
    evaluate.run(s, k=args.k, with_llm=args.llm, name=args.set)


def main(argv=None):
    p = argparse.ArgumentParser(prog="pcbrag")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ingest")
    i.add_argument("--recreate", action="store_true", help="drop and recreate the azure index")
    a = sub.add_parser("ask")
    a.add_argument("question", nargs="+")
    a.add_argument("-k", type=int, default=None)
    sub.add_parser("chat")
    sub.add_parser("stats")
    e = sub.add_parser("eval")
    e.add_argument("-k", type=int, default=5)
    e.add_argument("--llm", action="store_true", help="also check the generated answers (costs tokens)")
    e.add_argument("--set", default="questions", help="questions (default) or questions_hard")
    args = p.parse_args(argv)

    s = Settings()
    {"ingest": cmd_ingest, "ask": cmd_ask, "chat": cmd_chat, "stats": cmd_stats, "eval": cmd_eval}[args.cmd](s, args)


if __name__ == "__main__":
    sys.exit(main())
