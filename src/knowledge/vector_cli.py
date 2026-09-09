"""Run with python -m src.knowledge.vector_cli index|search|status."""

import argparse
import json
import time
from pathlib import Path

from src.config import PROJECT_ROOT
from .embedding import LocalEmbedding
from .retrieval import chunks, current, index, search
from .store import KnowledgeStore


def main():
    parser = argparse.ArgumentParser(description="本地中文向量索引与检索；首次使用下载模型")
    parser.add_argument("command", choices=["index", "search", "status"])
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--db", type=Path, default=PROJECT_ROOT / "data/jason_knowledge.db")
    parser.add_argument("--cache", type=Path, default=PROJECT_ROOT / "data/models")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=-1)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error("知识库不存在，请先导入文章")
    if args.command == "search" and not args.query.strip():
        parser.error("search 需要非空问题")
    provider = LocalEmbedding(args.cache)
    store = KnowledgeStore(args.db)
    started = time.perf_counter()
    try:
        if args.command == "index":
            result = index(store, provider)
        elif args.command == "search":
            result = {"query": args.query, "hits": search(store, provider, args.query, args.top_k, args.min_score)}
        else:
            rows = chunks(store)
            valid = sum(current(row, provider) for row in rows)
            result = {**store.stats(), "indexed_current": valid, "pending": len(rows) - valid,
                      "model": provider.model_id}
        result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    finally:
        store.close()
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
