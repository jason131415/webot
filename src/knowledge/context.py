"""Read-only, bounded knowledge context for conversational replies."""

from dataclasses import dataclass, field
from functools import lru_cache
import logging
from pathlib import Path
import sqlite3
import threading
from types import SimpleNamespace
from urllib.parse import urlsplit

from .embedding import LocalEmbedding
from .retrieval import search

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeContext:
    status: str
    sources: list[dict] = field(default_factory=list)

    def as_data(self):
        return {"status": self.status, "sources": self.sources}


class KnowledgeRetriever:
    def __init__(self, db_path, cache_dir, min_score=0.5, top_k=3, provider=None):
        if not 0 <= min_score <= 1 or not 1 <= top_k <= 5:
            raise ValueError("知识库 min_score 应为 0–1，top_k 应为 1–5")
        self.db_path = Path(db_path).resolve()
        self.provider = provider or LocalEmbedding(cache_dir, local_files_only=True)
        self.min_score, self.top_k = min_score, top_k
        self._lock = threading.Lock()

    def retrieve(self, query):
        if not query.strip():
            return KnowledgeContext("empty_query")
        if len(query) > 1000:
            return KnowledgeContext("query_too_long")
        if not self.db_path.is_file():
            return KnowledgeContext("unavailable")
        try:
            # Shared model is serialized; SQLite connection belongs to this request.
            with self._lock:
                conn = sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True, timeout=2)
                conn.row_factory = sqlite3.Row
                try:
                    conn.execute("BEGIN")
                    hits = search(SimpleNamespace(conn=conn), self.provider, query,
                                  self.top_k, self.min_score)
                    # Include bounded neighboring prose so a list is not cut at the index boundary.
                    for hit in hits:
                        row = conn.execute("""SELECT substr(a.content, max(c.start_offset-200,0)+1,1400)
                            FROM knowledge_chunks c JOIN articles a ON a.id=c.article_id WHERE c.id=?""",
                            (hit["chunk_id"],)).fetchone()
                        hit["content"] = row[0]
                finally:
                    conn.close()
            sources = []
            for hit in hits:
                parsed = urlsplit(hit["url"])
                if not hit["title"].strip() or parsed.scheme not in ("http", "https") or not parsed.netloc:
                    continue
                sources.append({"id": f"K{len(sources) + 1}", "title": hit["title"],
                    "url": hit["url"], "published_at": hit["published_at"], "source": hit["source"],
                    "content": hit["content"], "score": round(hit["score"], 6)})
            return KnowledgeContext("matched" if sources else "no_match", sources)
        except Exception as error:
            # No source text, user question, paths or API secrets in error logs.
            logger.warning("Knowledge retrieval unavailable (%s); using general chat", type(error).__name__)
            return KnowledgeContext("unavailable")


@lru_cache(maxsize=4)
def get_retriever(db_path, cache_dir, min_score=0.5, top_k=3):
    return KnowledgeRetriever(db_path, cache_dir, min_score, top_k)
