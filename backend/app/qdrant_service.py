import uuid
import traceback
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL
from app.embedding import build_embedding_text, embed_texts, embedding_dimension, embedding_model_label


def _collection_status_value(collection: Any) -> str:
    status = collection.status
    return status.value if hasattr(status, "value") else str(status)


def _exception_payload(exc: Exception) -> dict[str, Any]:
    return {
        "detail": str(exc),
        "error_type": exc.__class__.__name__,
        "error_traceback": traceback.format_exc(),
    }


def client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def point_id_for_isbn(isbn: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"book:{isbn}"))


def ensure_collection() -> str:
    qdrant = client()
    expected_size = embedding_dimension()
    try:
        collection = qdrant.get_collection(QDRANT_COLLECTION)
        vectors_config = collection.config.params.vectors
        if isinstance(vectors_config, dict):
            actual_size = next(iter(vectors_config.values())).size
        else:
            actual_size = vectors_config.size
        if actual_size != expected_size:
            raise ValueError(
                f"Qdrant collection '{QDRANT_COLLECTION}' vector dimension mismatch: "
                f"collection expects {actual_size}, embedding model '{embedding_model_label()}' outputs {expected_size}. "
                "請改用相同維度的 embedding model，或重建 collection。"
            )
        return _collection_status_value(collection)
    except Exception:
        if qdrant.collection_exists(QDRANT_COLLECTION):
            raise
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=expected_size, distance=Distance.COSINE),
        )
        return "created"


def collection_health() -> dict[str, Any]:
    qdrant = client()
    try:
        collections = qdrant.get_collections().collections
        names = sorted(collection.name for collection in collections)
        if QDRANT_COLLECTION not in set(names):
            return {
                "qdrant_status": "ok",
                "collection_status": "missing",
                "available_collections": names,
                "detail": f"找不到 collection '{QDRANT_COLLECTION}'，目前可用 collections: {', '.join(names) or '(none)'}",
            }
        collection = qdrant.get_collection(QDRANT_COLLECTION)
        return {
            "qdrant_status": "ok",
            "collection_status": _collection_status_value(collection),
            "available_collections": names,
            "detail": None,
        }
    except Exception as exc:
        return {
            "qdrant_status": "error",
            "collection_status": "error",
            "available_collections": [],
            **_exception_payload(exc),
        }


def existing_point_ids(point_ids: list[str]) -> set[str]:
    if not point_ids:
        return set()
    qdrant = client()
    points = qdrant.retrieve(collection_name=QDRANT_COLLECTION, ids=point_ids, with_vectors=False)
    return {str(point.id) for point in points}


def import_books(
    books: list[dict[str, Any]],
    duplicate_policy: str,
    batch_size: int,
) -> tuple[int, int, list[dict[str, Any]]]:
    ensure_collection()
    qdrant = client()
    success = 0
    failed = 0
    errors: list[dict[str, Any]] = []

    for offset in range(0, len(books), batch_size):
        batch = books[offset : offset + batch_size]
        ids = [point_id_for_isbn(book["isbn"]) for book in batch]
        if duplicate_policy in {"skip", "reject"}:
            existing = existing_point_ids(ids)
            if duplicate_policy == "reject" and existing:
                failed += len(batch)
                errors.append({"offset": offset, "code": "duplicate_in_qdrant", "message": "Qdrant 已存在相同 ISBN"})
                continue
            batch = [book for book, point_id in zip(batch, ids) if point_id not in existing]
            ids = [point_id_for_isbn(book["isbn"]) for book in batch]

        if not batch:
            continue

        texts = [build_embedding_text(book) for book in batch]
        vectors = embed_texts(texts)
        points = []
        for book, point_id, vector in zip(batch, ids, vectors):
            payload = book["source_data"]
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        try:
            qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points, wait=True)
            success += len(points)
        except Exception as exc:
            failed += len(points)
            errors.append({"offset": offset, "code": "qdrant_upsert_failed", "message": str(exc)})

    return success, failed, errors
