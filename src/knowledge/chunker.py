"""Deterministic character chunks with offsets into normalized article text."""


def normalize_content(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n").strip()


def chunk_text(content: str, size: int = 800, overlap: int = 100) -> list[tuple[int, int, str]]:
    """Keep every character, preferring paragraph boundaries when possible."""
    if size < 1 or not 0 <= overlap < size:
        raise ValueError("Require size > 0 and 0 <= overlap < size")
    chunks = []
    start = 0
    while start < len(content):
        end = min(start + size, len(content))
        if end < len(content):
            boundary = content.rfind("\n", start + max(overlap + 1, size // 2), end)
            if boundary != -1:
                end = boundary + 1
        chunks.append((start, end, content[start:end]))
        if end == len(content):
            break
        start = end - overlap
    return chunks
