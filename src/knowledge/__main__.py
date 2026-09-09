"""Usage: python -m src.knowledge articles_full.csv [--db PATH] [--report PATH]."""

import argparse
import json
from pathlib import Path

from src.config import PROJECT_ROOT
from .importer import read_articles
from .store import KnowledgeStore


def main() -> int:
    parser = argparse.ArgumentParser(description="导入本地公众号 CSV；不调用模型，不上传文章")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--db", type=Path, default=PROJECT_ROOT / "data/jason_knowledge.db")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    records, errors, digest = read_articles(args.csv)
    report = {
        "source_sha256": digest, "valid_rows": len(records), "errors": errors,
        "duplicate_keys": len(records) - len({r["article_key"] for r in records}),
        "missing_body": [{"source_id": r["source_id"], "title": r["title"], "url": r["url"]} for r in records if not r["content"]],
        "missing_title": [r["source_id"] for r in records if not r["title"]],
        "dry_run": args.dry_run,
    }
    if not args.dry_run:
        store = KnowledgeStore(args.db)
        try:
            report["import"] = store.import_articles(records)
        finally:
            store.close()
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
