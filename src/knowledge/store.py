"""Transactional SQLite article store, separate from the live chat database."""

import hashlib
import sqlite3
from pathlib import Path

from .chunker import chunk_text

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    article_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL, url TEXT NOT NULL, content TEXT NOT NULL,
    author TEXT NOT NULL, published_at TEXT NOT NULL,
    source TEXT NOT NULL, source_id TEXT NOT NULL, biz TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ready', 'metadata_only')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL,
    content TEXT NOT NULL,
    UNIQUE(article_id, chunk_index)
);
"""


class KnowledgeStore:
    def __init__(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def import_articles(self, articles: list[dict]) -> dict:
        """Atomic batch upsert; unchanged bodies retain chunk IDs.

        An incomplete subsequent export cannot erase an existing full body.
        Only body changes regenerate all chunks in the same transaction.
        """
        counts = {"inserted": 0, "updated": 0, "unchanged": 0, "preserved_body": 0}
        fields = ("title", "url", "content", "author", "published_at", "source", "source_id", "biz", "metadata_json")
        with self.conn:
            for record in articles:
                item = dict(record)
                old = self.conn.execute("SELECT * FROM articles WHERE article_key=?", (item["article_key"],)).fetchone()
                if old and old["content"] and not item["content"]:
                    item["content"] = old["content"]
                    counts["preserved_body"] += 1
                if old and not item["title"]:
                    item["title"] = old["title"]
                body_hash = hashlib.sha256(item["content"].encode("utf-8")).hexdigest()
                status = "ready" if item["content"] else "metadata_only"
                if old and all(old[k] == item[k] for k in fields):
                    counts["unchanged"] += 1
                    continue
                if old:
                    self.conn.execute(
                        "UPDATE articles SET " + ",".join(f"{k}=?" for k in fields)
                        + ",content_hash=?,status=?,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                        (*[item[k] for k in fields], body_hash, status, old["id"]),
                    )
                    article_id = old["id"]
                    counts["updated"] += 1
                else:
                    cursor = self.conn.execute(
                        "INSERT INTO articles (article_key," + ",".join(fields) + ",content_hash,status) VALUES ("
                        + ",".join("?" for _ in range(len(fields) + 3)) + ")",
                        (item["article_key"], *[item[k] for k in fields], body_hash, status),
                    )
                    article_id = cursor.lastrowid
                    counts["inserted"] += 1
                if old is None or old["content_hash"] != body_hash:
                    self.conn.execute("DELETE FROM knowledge_chunks WHERE article_id=?", (article_id,))
                    self.conn.executemany(
                        "INSERT INTO knowledge_chunks (article_id,chunk_index,start_offset,end_offset,content) VALUES (?,?,?,?,?)",
                        [(article_id, i, start, end, text) for i, (start, end, text) in enumerate(chunk_text(item["content"]))],
                    )
        counts["totals"] = self.stats()
        return counts

    def stats(self) -> dict:
        return {
            "articles": self.conn.execute("SELECT count(*) FROM articles").fetchone()[0],
            "ready": self.conn.execute("SELECT count(*) FROM articles WHERE status='ready'").fetchone()[0],
            "metadata_only": self.conn.execute("SELECT count(*) FROM articles WHERE status='metadata_only'").fetchone()[0],
            "chunks": self.conn.execute("SELECT count(*) FROM knowledge_chunks").fetchone()[0],
        }
