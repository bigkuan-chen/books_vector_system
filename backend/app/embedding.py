import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from functools import lru_cache
from typing import Any

from app.config import (
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    EMBEDDING_NORMALIZE,
    EMBEDDING_PROVIDER,
    OLLAMA_EMBED_DIMENSIONS,
    OLLAMA_EMBED_MODEL,
    OLLAMA_URL,
)


EMBED_FIELDS = (
    "title",
    "subtitle",
    "authors",
    "publisher",
    "subjects",
    "keywords",
    "description",
    "summary",
    "table_of_contents",
)


def build_embedding_text(book: dict[str, Any]) -> str:
    source = book.get("source_data", {})
    values: dict[str, Any] = {**source, **book}
    lines: list[str] = []
    labels = {
        "title": "書名",
        "subtitle": "副標題",
        "authors": "作者",
        "publisher": "出版社",
        "subjects": "主題",
        "keywords": "關鍵字",
        "description": "簡介",
        "summary": "摘要",
        "table_of_contents": "目錄",
    }
    for field in EMBED_FIELDS:
        value = values.get(field)
        if value is None or value == "":
            continue
        if isinstance(value, list):
            text = "、".join(str(item) for item in value if str(item).strip())
        else:
            text = str(value).strip()
        if text:
            lines.append(f"{labels[field]}：{text}")
    return "\n".join(lines)[:12000]


def build_query_embedding_text(query: str) -> str:
    return f"query: {query.strip()}"


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)


def embedding_model_label() -> str:
    if EMBEDDING_PROVIDER == "ollama":
        return f"ollama:{OLLAMA_EMBED_MODEL}"
    return EMBEDDING_MODEL


def _ollama_embed_texts(texts: list[str]) -> list[list[float]]:
    payload: dict[str, Any] = {
        "model": OLLAMA_EMBED_MODEL,
        "input": texts,
        "truncate": True,
    }
    if OLLAMA_EMBED_DIMENSIONS > 0:
        payload["dimensions"] = OLLAMA_EMBED_DIMENSIONS

    request = Request(
        f"{OLLAMA_URL.rstrip('/')}/api/embed",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama embedding request failed: HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"無法連線 Ollama：{OLLAMA_URL}，請確認 Ollama 已啟動且模型已 pull：{OLLAMA_EMBED_MODEL}") from exc

    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings:
        raise RuntimeError(f"Ollama 回傳格式缺少 embeddings：{data}")
    return embeddings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if EMBEDDING_PROVIDER == "ollama":
        return _ollama_embed_texts(texts)
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=EMBEDDING_NORMALIZE, show_progress_bar=False)
    return vectors.tolist()


def embedding_dimension() -> int:
    if EMBEDDING_PROVIDER == "ollama" and OLLAMA_EMBED_DIMENSIONS > 0:
        return OLLAMA_EMBED_DIMENSIONS
    return len(embed_texts(["dimension probe"])[0])
