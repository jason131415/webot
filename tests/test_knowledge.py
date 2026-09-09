"""Synthetic article fixtures only; never commit the user's real content."""

import csv

import pytest

from src.knowledge.chunker import chunk_text, normalize_content
from src.knowledge.importer import article_key, read_articles
from src.knowledge.store import KnowledgeStore


def export(tmp_path, rows):
    path = tmp_path / "articles.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "标题", "正文", "原文链接", "source", "作者"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def article(content="测试正文", **values):
    return {"id": "1", "标题": "测试标题", "正文": content, "原文链接": "https://mp.weixin.qq.com/s/test", "source": "own", "作者": "测试作者", **values}


@pytest.fixture
def store(tmp_path):
    result = KnowledgeStore(tmp_path / "knowledge.db")
    yield result
    result.close()


def test_multiline_csv_unicode_and_provenance(tmp_path):
    rows, errors, digest = read_articles(export(tmp_path, [article('第一行,"引号"\n第二行😀')]))
    assert not errors and len(digest) == 64
    assert rows[0]["content"] == '第一行,"引号"\n第二行😀'
    assert rows[0]["source"] == "own" and rows[0]["author"] == "测试作者"


def test_missing_body_is_not_replaced_with_title(tmp_path, store):
    rows, _, _ = read_articles(export(tmp_path, [article("")]))
    result = store.import_articles(rows)
    assert result["totals"] == {"articles": 1, "ready": 0, "metadata_only": 1, "chunks": 0}


def test_bad_url_is_reported_and_other_rows_survive(tmp_path):
    rows, errors, _ = read_articles(export(tmp_path, [article(), article(原文链接="javascript:alert(1)")]))
    assert len(rows) == 1 and errors[0]["row"] == 3


def test_missing_headers_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("title,body\na,b", encoding="utf-8")
    with pytest.raises(ValueError, match="缺少"):
        read_articles(path)


def test_duplicate_headers_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("标题,正文,原文链接,正文\na,b,c,d", encoding="utf-8")
    with pytest.raises(ValueError, match="重复"):
        read_articles(path)


def test_wechat_tracking_parameters_do_not_change_identity():
    assert article_key("https://mp.weixin.qq.com/s/test?scene=1#abc") == article_key("https://mp.weixin.qq.com/s/test")
    assert article_key("https://mp.weixin.qq.com/s?__biz=abc&mid=12&idx=1&sn=old&scene=1") == article_key("https://mp.weixin.qq.com/s?idx=1&mid=12&__biz=abc&sn=new")


def test_chunks_preserve_content_offsets_and_limits():
    text = normalize_content(("段落，带中文😀\r\n" * 450) + "结尾")
    chunks = chunk_text(text)
    covered = set()
    for start, end, content in chunks:
        assert content == text[start:end] and 0 < len(content) <= 800
        covered.update(range(start, end))
    assert covered == set(range(len(text)))
    assert chunks[-1][1] == len(text)
    assert chunk_text("") == []


@pytest.mark.parametrize("size,overlap", [(0, 0), (10, 10), (10, -1)])
def test_bad_chunk_settings_rejected(size, overlap):
    with pytest.raises(ValueError):
        chunk_text("正文", size, overlap)


def test_repeat_import_is_idempotent_and_retains_chunks(tmp_path, store):
    rows, _, _ = read_articles(export(tmp_path, [article("测试\n" * 1000)]))
    assert store.import_articles(rows)["inserted"] == 1
    before = [tuple(r) for r in store.conn.execute("SELECT * FROM knowledge_chunks")]
    assert store.import_articles(rows)["unchanged"] == 1
    assert before == [tuple(r) for r in store.conn.execute("SELECT * FROM knowledge_chunks")]


def test_changed_body_replaces_chunks_atomically(tmp_path, store):
    rows, _, _ = read_articles(export(tmp_path, [article("旧内容" * 1000)]))
    store.import_articles(rows)
    original_id = store.conn.execute("SELECT id FROM articles").fetchone()[0]
    rows[0]["content"] = "新内容"
    assert store.import_articles(rows)["updated"] == 1
    assert store.conn.execute("SELECT id FROM articles").fetchone()[0] == original_id
    assert [r[0] for r in store.conn.execute("SELECT content FROM knowledge_chunks")] == ["新内容"]


def test_incomplete_later_export_does_not_erase_body(tmp_path, store):
    rows, _, _ = read_articles(export(tmp_path, [article()]))
    store.import_articles(rows)
    rows[0]["content"] = ""
    result = store.import_articles(rows)
    assert result["preserved_body"] == 1
    assert store.conn.execute("SELECT content FROM articles").fetchone()[0] == "测试正文"
    assert result["totals"]["ready"] == 1


def test_failed_batch_rolls_back_all_rows(tmp_path, store, monkeypatch):
    rows, _, _ = read_articles(export(tmp_path, [article()]))
    import src.knowledge.store as module
    monkeypatch.setattr(module, "chunk_text", lambda _: (_ for _ in ()).throw(RuntimeError("failed")))
    with pytest.raises(RuntimeError):
        store.import_articles(rows)
    assert store.stats()["articles"] == 0


def test_cascade_delete_does_not_leave_orphan_chunks(tmp_path, store):
    rows, _, _ = read_articles(export(tmp_path, [article()]))
    store.import_articles(rows)
    with store.conn:
        store.conn.execute("DELETE FROM articles")
    assert store.stats()["chunks"] == 0
    assert store.conn.execute("PRAGMA foreign_key_check").fetchall() == []
