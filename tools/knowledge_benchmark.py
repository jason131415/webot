"""Local-only Phase 3 smoke/latency report. Run from the repository root."""

import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["HF_HUB_OFFLINE"] = "1"
import psutil
from src.knowledge.embedding import LocalEmbedding, split_for_model
from src.knowledge.retrieval import chunks, index, search
from src.knowledge.store import KnowledgeStore


def main():
    root = Path(__file__).resolve().parents[1]
    provider = LocalEmbedding(root / "data/models")
    store = KnowledgeStore(root / "data/jason_knowledge.db")
    process = psutil.Process()
    report = {"offline": True, "queries": [], "initial_rss_mb": round(process.memory_info().rss / 2**20, 1)}
    try:
        started = time.perf_counter()
        report["repeat_index"] = index(store, provider)
        report["repeat_index_seconds"] = round(time.perf_counter() - started, 3)
        for query in ["DeepSeek Harness 和 Agent Skills 有什么区别？", "AI 如何帮助我提高写作效率？",
                      "Google 开源的 AI Agent 如何使用向量数据库？", "如何让 AI 自动完成任务而不用逐步指导？",
                      "番茄炒蛋应该放多少盐？"]:
            started = time.perf_counter()
            hits = search(store, provider, query, top_k=3)
            report["queries"].append({"query": query, "seconds": round(time.perf_counter() - started, 3),
                "hits": [{k: h[k] for k in ("title", "url", "score", "chunk_id")} for h in hits]})
        # Every title/body input must survive splitting byte-for-byte with no truncation.
        checked, max_tokens, split_count = 0, 0, 0
        for row in chunks(store):
            text = row["title"] + "\n" + row["content"]
            pieces = split_for_model(text, provider._tokenizer)
            assert "".join(pieces) == text
            lengths = [len(provider._tokenizer.encode(p, add_special_tokens=False).ids) for p in pieces]
            assert max(lengths) <= 480
            max_tokens = max(max_tokens, max(lengths))
            split_count += len(pieces) > 1
            checked += 1
        report["length_validation"] = {"checked_chunks": checked, "split_chunks": split_count, "max_window_tokens": max_tokens}
        report["integrity"] = store.conn.execute("PRAGMA integrity_check").fetchone()[0]
        report["foreign_key_errors"] = len(store.conn.execute("PRAGMA foreign_key_check").fetchall())
        memory = process.memory_info()
        report["rss_mb"] = round(memory.rss / 2**20, 1)
        report["peak_rss_mb"] = round(getattr(memory, "peak_wset", memory.rss) / 2**20, 1)
        report["model_files_mb"] = round(sum(p.stat().st_size for p in (root / "data/models").rglob("*") if p.is_file()) / 2**20, 1)
    finally:
        store.close()
    output = json.dumps(report, ensure_ascii=False, indent=2)
    (root / "outputs/phase3-benchmark.json").write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
