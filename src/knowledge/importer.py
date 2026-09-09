"""Read an exported article CSV as data, never as executable instructions."""

import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from .chunker import normalize_content


def article_key(url: str) -> str:
    """Canonical identity for WeChat links; keep the original URL for citations."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc or parts.username or parts.password:
        raise ValueError("原文链接必须是有效的 HTTP(S) URL")
    query = parts.query
    if parts.hostname == "mp.weixin.qq.com":
        fields = parse_qs(query)
        if parts.path.rstrip("/") == "/s" and all(fields.get(k) for k in ("__biz", "mid", "idx")):
            query = urlencode({k: fields[k][0] for k in ("__biz", "mid", "idx")})
        elif parts.path.startswith("/s/"):
            query = ""
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, query, ""))


def read_articles(path: str | Path) -> tuple[list[dict], list[dict], str]:
    """Return valid records, row errors and a source-file checksum.

    UTF-8 with/without BOM, quoted commas and multiline bodies are supported.
    Missing title/body remains explicit; abstracts never substitute for bodies.
    """
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    articles, errors = [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        required = {"标题", "原文链接", "正文"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV 缺少必需字段：标题、原文链接、正文")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("CSV 字段名重复")
        for row_number, row in enumerate(reader, 2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("列数与表头不一致")
                url = row["原文链接"].strip()
                record = {
                    "article_key": article_key(url),
                    "title": row["标题"].strip(), "url": url,
                    "content": normalize_content(row["正文"]),
                    "author": row.get("作者", "").strip(),
                    "published_at": row.get("发布时间", "").strip(),
                    "source": row.get("source", "").strip(),
                    "source_id": row.get("id", "").strip(),
                    "biz": row.get("biz", "").strip(),
                    "row_number": row_number,
                }
                # Raw metadata retains every field, but avoid duplicating large bodies.
                metadata = dict(row)
                metadata.pop("正文", None)
                record["metadata_json"] = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
                articles.append(record)
            except ValueError as exc:
                errors.append({"row": row_number, "source_id": row.get("id", ""), "error": str(exc)})
    return articles, errors, digest
