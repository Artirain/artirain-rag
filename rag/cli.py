import argparse
import sys

from .config import load_config
from .ingest import ingest
from .query import answer


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="rag")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest", help="index documents from data dir into Qdrant")
    ask = sub.add_parser("ask", help="ask a question over the indexed docs")
    ask.add_argument("question")
    args = parser.parse_args()

    cfg = load_config()
    if args.cmd == "ingest":
        n = ingest(cfg)
        print(f"indexed {n} chunks into '{cfg.collection}'")
    elif args.cmd == "ask":
        res = answer(args.question, cfg)
        print(res["answer"])
        print("\nsources:", ", ".join(res["sources"]))


if __name__ == "__main__":
    main()
