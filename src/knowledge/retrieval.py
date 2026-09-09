"""Resumable local vector index; source text is never sent over the network."""

import hashlib
import json
import math


def normalized(vector, dimension=None):
    values = [float(v) for v in vector]
    if not values or (dimension is not None and len(values) != dimension):
        raise ValueError("向量维度不匹配")
    if not all(math.isfinite(v) for v in values):
        raise ValueError("向量包含非有限数值")
    norm = math.sqrt(sum(v * v for v in values))
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("向量范数无效")
    return [v / norm for v in values]


def source_text(row):
    return row["title"] + "\n" + row["content"]


def source_hash(row):
    return hashlib.sha256(source_text(row).encode("utf-8")).hexdigest()


def chunks(store):
    return store.conn.execute("""SELECT c.*, a.title, a.url, a.published_at, a.source
        FROM knowledge_chunks c JOIN articles a ON a.id=c.article_id ORDER BY c.id""").fetchall()


def current(row, provider):
    return (row["embedding_json"] is not None
            and row["embedding_model"] == provider.model_id
            and row["embedding_dimension"] == provider.dimension
            and row["embedding_hash"] == source_hash(row))


def index(store, provider, batch_size=8):
    """Commit one validated batch at a time; failed batches remain retryable."""
    if batch_size < 1:
        raise ValueError("batch_size 必须为正数")
    rows = chunks(store)
    pending = [row for row in rows if not current(row, provider)]
    written = 0
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        vectors = list(provider.embed([source_text(row) for row in batch]))
        if len(vectors) != len(batch):
            raise ValueError("向量数量与片段数量不匹配")
        vectors = [normalized(v, provider.dimension) for v in vectors]
        with store.conn:
            for row, vector in zip(batch, vectors):
                # A concurrently edited article must never receive a stale vector.
                fresh = store.conn.execute("""SELECT c.*, a.title FROM knowledge_chunks c
                    JOIN articles a ON a.id=c.article_id WHERE c.id=?""", (row["id"],)).fetchone()
                if fresh is None or source_hash(fresh) != source_hash(row):
                    raise ValueError("索引期间文章已变更，请重试")
                store.conn.execute("""UPDATE knowledge_chunks SET embedding_json=?,
                    embedding_model=?,embedding_dimension=?,embedding_hash=?,
                    embedded_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?""",
                    (json.dumps(vector), provider.model_id, provider.dimension, source_hash(row), row["id"]))
        written += len(batch)
    return {"chunks": len(rows), "indexed": written, "unchanged": len(rows) - len(pending),
            "model": provider.model_id, "dimension": provider.dimension}


def search(store, provider, query, top_k=5, min_score=-1.0):
    """Cosine similarity, best chunk per article, with original provenance."""
    if not query.strip():
        return []
    if not 1 <= top_k <= 100 or not math.isfinite(min_score) or not -1 <= min_score <= 1:
        raise ValueError("top_k 应为 1–100，min_score 应为 -1–1")
    rows = [row for row in chunks(store) if current(row, provider)]
    if not rows:
        return []
    q = normalized(provider.query(query), provider.dimension)
    hits = []
    for row in rows:
        vector = normalized(json.loads(row["embedding_json"]), provider.dimension)
        score = max(-1.0, min(1.0, sum(a * b for a, b in zip(q, vector))))
        if score >= min_score:
            hits.append({"article_id": row["article_id"], "chunk_id": row["id"],
                         "title": row["title"], "url": row["url"], "content": row["content"],
                         "published_at": row["published_at"], "source": row["source"], "score": score})
    hits.sort(key=lambda h: (-h["score"], h["chunk_id"]))
    result, seen = [], set()
    for hit in hits:
        if hit["article_id"] not in seen:
            result.append(hit)
            seen.add(hit["article_id"])
            if len(result) == top_k:
                break
    return result
