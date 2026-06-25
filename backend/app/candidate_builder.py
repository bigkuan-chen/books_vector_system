from dataclasses import dataclass
from typing import Any


def get_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def first_payload_value(payload: dict[str, Any], paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = get_path(payload, path)
        if value not in (None, ""):
            return value
    return None


def payload_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [payload]
    for key in ("source_data", "payload", "data", "metadata", "book"):
        value = payload.get(key)
        if isinstance(value, dict):
            sources.append(value)
    return sources


def first_value(payload: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for source in payload_sources(payload):
        lower_keys = {key.lower(): key for key in source.keys()}
        for alias in aliases:
            if alias in source and source[alias] not in (None, ""):
                return source[alias]
            found_key = lower_keys.get(alias.lower())
            if found_key is not None and source[found_key] not in (None, ""):
                return source[found_key]
    nested_paths = tuple(
        f"{container}.{alias}"
        for container in ("source_data", "payload", "data", "metadata", "book")
        for alias in aliases
    )
    return first_payload_value(payload, nested_paths)


def list_value(value: Any, limit: int) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item).strip()[:500] for item in value if str(item).strip()][:limit]
    return [str(value).strip()[:500]]


def text_value(value: Any, max_chars: int) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip()[:max_chars]


@dataclass
class Candidate:
    candidate_id: str
    point_id: str
    isbn: str
    title: str | None
    authors: list[str]
    publisher: str | None
    publish_date: str | None
    language: str | None
    subjects: list[str]
    description: str | None
    vector_score: float
    payload: dict[str, Any]

    def for_llm(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "isbn": self.isbn,
            "title": self.title,
            "authors": self.authors,
            "publisher": self.publisher,
            "publish_date": self.publish_date,
            "language": self.language,
            "subjects": self.subjects,
            "description": self.description,
            "vector_score": self.vector_score,
        }


def build_candidates(points: list[Any]) -> list[Candidate]:
    candidates: list[Candidate] = []
    seen_isbns: set[str] = set()
    for point in points:
        payload = point.payload if isinstance(point.payload, dict) else {}
        isbn = text_value(first_value(payload, ("isbn", "ISBN", "_ISBN標準化", "_ISBN標準化", "isbn13", "ISBN13")), 100)
        if not isbn or isbn in seen_isbns:
            continue
        seen_isbns.add(isbn)
        candidates.append(
            Candidate(
                candidate_id=f"C{len(candidates) + 1:02d}",
                point_id=str(point.id),
                isbn=isbn,
                title=text_value(first_value(payload, ("title", "申請書名", "書名", "book_title", "name")), 500),
                authors=list_value(first_value(payload, ("authors", "author", "作者", "creator", "creators")), 20),
                publisher=text_value(first_value(payload, ("publisher", "出版機構", "出版社")), 500),
                publish_date=text_value(first_value(payload, ("publish_date", "published_at", "出版日期", "預訂出版日")), 100),
                language=text_value(first_value(payload, ("language", "lang", "作品語文")), 50),
                subjects=list_value(first_value(payload, ("subjects", "subject", "categories", "category", "圖書主題", "建議上架分類")), 30),
                description=text_value(
                    first_value(payload, ("description", "summary", "content", "標題", "關鍵字", "簡介", "內容簡介")),
                    2000,
                ),
                vector_score=float(getattr(point, "score", 1.0) or 0),
                payload=payload,
            )
        )
    return candidates
