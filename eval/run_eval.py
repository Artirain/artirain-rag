import argparse
import json
import os
import time

from rag.config import load_config
from rag.query import answer
from rag.store import Store


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def eval_retrieval(cfg, dataset):
    store = Store(cfg)
    hits_at_k = 0
    latencies = []
    for row in dataset:
        t0 = time.perf_counter()
        results = store.search(row["question"])
        latencies.append((time.perf_counter() - t0) * 1000)
        sources = {r["source"] for r in results}
        if row["expected_source"] in sources:
            hits_at_k += 1
    return hits_at_k / len(dataset), sorted(latencies)


def eval_answers(cfg, dataset):
    ok = 0
    for row in dataset:
        res = answer(row["question"], cfg)
        text = res["answer"].lower()
        if all(kw.lower() in text for kw in row.get("keywords", [])):
            ok += 1
    return ok / len(dataset)


def p50(values):
    return values[len(values) // 2] if values else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=os.path.join("eval", "dataset.jsonl"))
    parser.add_argument("--answers", action="store_true",
                        help="also score generated answers via LLM (slower)")
    args = parser.parse_args()

    cfg = load_config()
    dataset = load_dataset(args.dataset)

    hit_rate, latencies = eval_retrieval(cfg, dataset)
    print(f"retrieval hit@{cfg.top_k}: {hit_rate:.0%}  ({len(dataset)} questions)")
    print(f"retrieval latency p50: {p50(latencies):.0f} ms  max: {max(latencies):.0f} ms")

    if args.answers:
        acc = eval_answers(cfg, dataset)
        print(f"answer keyword accuracy: {acc:.0%}")


if __name__ == "__main__":
    main()
