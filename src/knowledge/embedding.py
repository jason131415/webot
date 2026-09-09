"""CPU-only Chinese embedding, lazily loaded and cached in the project."""

from .retrieval import normalized


def split_for_model(text, tokenizer, limit=480):
    """Lossless character windows bounded by actual untruncated token counts."""
    if len(tokenizer.encode(text, add_special_tokens=False).ids) <= limit:
        return [text]
    if len(text) < 2:
        raise ValueError("单字符超过模型上下文限制")
    middle = len(text) // 2
    return split_for_model(text[:middle], tokenizer, limit) + split_for_model(text[middle:], tokenizer, limit)


class LocalEmbedding:
    model_name = "BAAI/bge-small-zh-v1.5"
    # Fingerprint includes preprocessing and query instruction, not just weights.
    model_id = "BAAI/bge-small-zh-v1.5:fastembed0.8:char-bisect480:weighted-mean-v1:query-zh"
    dimension = 512

    def __init__(self, cache_dir, threads=4, local_files_only=False):
        self.cache_dir = str(cache_dir)
        self.threads = threads
        self.local_files_only = local_files_only
        self._model = None
        self._tokenizer = None

    def _load(self):
        if self._model is None:
            from fastembed import TextEmbedding
            from tokenizers import Tokenizer
            self._model = TextEmbedding(model_name=self.model_name, cache_dir=self.cache_dir,
                                        threads=self.threads, providers=["CPUExecutionProvider"],
                                        local_files_only=self.local_files_only)
            self._tokenizer = Tokenizer.from_str(self._model.model.tokenizer.to_str())
            self._tokenizer.no_truncation()
            self._tokenizer.no_padding()

    def embed(self, texts):
        self._load()
        for text in texts:
            pieces = split_for_model(text, self._tokenizer)
            vectors = list(self._model.embed(pieces, batch_size=8))
            weights = [max(1, len(self._tokenizer.encode(p, add_special_tokens=False).ids)) for p in pieces]
            pooled = [sum(float(v[i]) * w for v, w in zip(vectors, weights)) / sum(weights)
                      for i in range(self.dimension)]
            yield normalized(pooled, self.dimension)

    def query(self, text):
        return next(self.embed(["为这个句子生成表示以用于检索相关文章：" + text]))
