"""Index lifecycle and retrieval correctness, without network or model downloads."""

import json
from types import SimpleNamespace

import pytest

from src.knowledge.embedding import split_for_model
from src.knowledge.retrieval import index, search, normalized
from src.knowledge.store import KnowledgeStore


class FakeEmbedding:
    model_id = "test-v1"
    dimension = 2

    def __init__(self):
        self.calls = 0
        self.fail_at = None

    def embed(self, texts):
        self.calls += 1
        if self.calls == self.fail_at:
            raise RuntimeError("temporary failure")
        return [[1, 0] if "苹果" in text else [0, 1] for text in texts]

    def query(self, text):
        return self.embed([text])[0]


def record(key, content, title="测试"):
    return dict(article_key=key, title=title, url="https://example.com/" + key,
                content=content, author="作者", published_at="2026-01-01", source="own",
                source_id=key, biz="", metadata_json="{}")


@pytest.fixture
def store(tmp_path):
    store = KnowledgeStore(tmp_path / "test.db")
    store.import_articles([record("a", "苹果" * 600), record("b", "香蕉"), record("c", "")])
    yield store
    store.close()


def test_index_incremental_and_provenance(store):
    provider = FakeEmbedding()
    first = index(store, provider)
    assert first["indexed"] == store.stats()["chunks"]
    calls = provider.calls
    assert index(store, provider)["indexed"] == 0
    assert provider.calls == calls
    hits = search(store, provider, "苹果", top_k=2)
    assert len(hits) == 2 and hits[0]["score"] == 1
    assert hits[0]["url"] == "https://example.com/a"
    assert hits[0]["title"] == "测试" and hits[0]["source"] == "own"
    assert len({h["article_id"] for h in hits}) == 2
    assert len(search(store, provider, "苹果", min_score=0.5)) == 1


def test_title_change_invalidates_vectors(store):
    provider = FakeEmbedding()
    index(store, provider)
    store.import_articles([record("a", "苹果" * 600, "新标题")])
    assert all(h["url"] != "https://example.com/a" for h in search(store, provider, "苹果"))
    assert index(store, provider)["indexed"] == 2
    assert search(store, provider, "苹果")[0]["title"] == "新标题"


def test_body_change_removes_old_vectors(store):
    provider = FakeEmbedding()
    index(store, provider)
    store.import_articles([record("a", "新正文")])
    assert store.conn.execute("SELECT count(*) FROM knowledge_chunks WHERE embedding_json IS NULL").fetchone()[0] == 1
    assert index(store, provider)["indexed"] == 1
    assert store.conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_partial_failure_resumes(store):
    provider = FakeEmbedding()
    provider.fail_at = 2
    with pytest.raises(RuntimeError):
        index(store, provider, batch_size=1)
    assert store.conn.execute("SELECT count(*) FROM knowledge_chunks WHERE embedding_json IS NOT NULL").fetchone()[0] == 1
    provider.fail_at = None
    result = index(store, provider, batch_size=1)
    assert result["unchanged"] == 1 and result["indexed"] == 2


def test_model_and_dimension_never_mix(store):
    provider = FakeEmbedding()
    index(store, provider)
    provider.model_id = "test-v2"
    assert search(store, provider, "苹果") == []
    assert index(store, provider)["indexed"] == 3
    provider.dimension = 3
    assert search(store, provider, "苹果") == []
    with pytest.raises(ValueError, match="维度"):
        index(store, provider)


@pytest.mark.parametrize("values", [[], [0, 0], [float('nan'), 0], [float('inf'), 1], [1, 2, 3]])
def test_reject_invalid_vectors(values):
    with pytest.raises(ValueError):
        normalized(values, 2)


@pytest.mark.parametrize("vectors", [[], [[1, 0]], [[1, 0], [0, 0], [0, 1]]])
def test_invalid_batch_is_atomic(store, vectors):
    provider = FakeEmbedding()
    provider.embed = lambda texts: vectors
    with pytest.raises(ValueError):
        index(store, provider)
    assert store.conn.execute("SELECT count(*) FROM knowledge_chunks WHERE embedding_json IS NOT NULL").fetchone()[0] == 0


def test_empty_query_or_index_does_not_load_model(store):
    provider = FakeEmbedding()
    assert search(store, provider, "苹果") == []
    assert search(store, provider, "  ") == []
    assert provider.calls == 0


def test_corrupt_stored_dimension_rejected(store):
    provider = FakeEmbedding()
    index(store, provider)
    store.conn.execute("UPDATE knowledge_chunks SET embedding_json='[1,2,3]'")
    with pytest.raises(ValueError, match="维度"):
        search(store, provider, "苹果")


def test_length_windows_preserve_tail_and_unicode():
    class Tokenizer:
        def encode(self, text, add_special_tokens=False):
            return SimpleNamespace(ids=list(text.encode("utf-8")))
    text = ("中文😀code\n" * 200) + "尾部不能丢失"
    parts = split_for_model(text, Tokenizer())
    assert "".join(parts) == text
    assert len(parts) > 1
    assert all(len(p.encode("utf-8")) <= 480 for p in parts)


def test_migration_preserves_old_chunks(tmp_path):
    import sqlite3
    from src.knowledge.store import SCHEMA
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript(SCHEMA)
    old.close()
    store = KnowledgeStore(path)
    store.import_articles([record("a", "正文")])
    before = tuple(store.conn.execute("SELECT id,article_id,content FROM knowledge_chunks").fetchone())
    store.close()
    store = KnowledgeStore(path)
    assert tuple(store.conn.execute("SELECT id,article_id,content FROM knowledge_chunks").fetchone()) == before
    assert store.conn.execute("SELECT embedding_json FROM knowledge_chunks").fetchone()[0] is None
    store.close()
