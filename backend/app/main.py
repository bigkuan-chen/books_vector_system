import os

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import BOOK_QUERY_API_KEY, IMPORT_BATCH_SIZE, QDRANT_COLLECTION, QDRANT_URL
from app.embedding import embedding_model_label
from app.llm_reranker import is_configured as llm_is_configured
from app.qdrant_service import collection_health, import_books
from app.schemas import (
    BookSearchHealthResponse,
    BookSearchRequest,
    BookSearchResponse,
    HealthResponse,
    ImportExecuteRequest,
    ImportStatus,
    ServiceHealth,
    ValidationSummary,
)
from app.search_orchestrator import search
from app.storage import import_store, validation_store
from app.validation import parse_uploaded_json, validate_records


app = FastAPI(title="Book Vector Query API", version="MVP-v3")

frontend_urls = os.getenv(
    "FRONTEND_URLS",
)

allowed_origins = [
    url.strip()
    for url in frontend_urls.split(",")
    if url.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not BOOK_QUERY_API_KEY or BOOK_QUERY_API_KEY == "change-me":
        return
    if x_api_key != BOOK_QUERY_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/api/health/qdrant", response_model=HealthResponse)
def qdrant_health() -> HealthResponse:
    health = collection_health()
    return HealthResponse(
        qdrant_status=health["qdrant_status"],
        qdrant_url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
        collection_status=health["collection_status"],
        dashboard_url=f"{QDRANT_URL}/dashboard#/collections/{QDRANT_COLLECTION}",
        available_collections=health.get("available_collections", []),
        detail=health.get("detail"),
        error_type=health.get("error_type"),
        error_traceback=health.get("error_traceback"),
    )


@app.get("/api/health", response_model=BookSearchHealthResponse)
def book_search_health() -> BookSearchHealthResponse:
    health = collection_health()
    qdrant_ok = health["qdrant_status"] == "ok" and health["collection_status"] != "missing"
    return BookSearchHealthResponse(
        success=qdrant_ok,
        services={
            "api": ServiceHealth(status="healthy"),
            "embedding": ServiceHealth(status="healthy", model=embedding_model_label()),
            "qdrant": ServiceHealth(
                status="healthy" if qdrant_ok else "unhealthy",
                container="books_container",
                collection=QDRANT_COLLECTION,
                detail=health.get("detail"),
            ),
            "llm": ServiceHealth(status="healthy" if llm_is_configured() else "not_configured"),
        },
    )


@app.post(
    "/api/books/search",
    response_model=BookSearchResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(require_api_key)],
)
def book_search(request: BookSearchRequest) -> BookSearchResponse:
    try:
        return search(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/import/validate", response_model=ValidationSummary)
async def validate_file(file: UploadFile = File(...)) -> ValidationSummary:
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="只接受 .json 檔案")

    content = await file.read()
    records, parse_messages = parse_uploaded_json(content, file.filename)
    if parse_messages and any(message.severity == "error" for message in parse_messages):
        summary = ValidationSummary(
            validation_id="",
            filename=file.filename,
            total_records=0,
            valid_records=0,
            warning_records=0,
            invalid_records=0,
            duplicate_records=0,
            importable=False,
            messages=parse_messages,
        )
        return summary

    summary, normalized_records = validate_records(records, file.filename)
    summary.messages.extend(parse_messages)
    validation_store[summary.validation_id] = {
        "summary": summary,
        "records": normalized_records,
    }
    return summary


@app.post("/api/import/execute", response_model=ImportStatus)
def execute_import(request: ImportExecuteRequest) -> ImportStatus:
    stored = validation_store.get(request.validation_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="找不到 validation_id，請重新檢查檔案")

    records = stored["records"]
    summary: ValidationSummary = stored["summary"]
    invalid_count = sum(1 for record in records if not record["is_valid"])
    if request.import_mode == "all_or_nothing" and invalid_count:
        raise HTTPException(status_code=400, detail="all_or_nothing 模式下不可有錯誤資料")

    importable = [record for record in records if record["is_valid"]]
    batch_id = importable[0]["import_batch_id"] if importable else request.validation_id
    status = ImportStatus(
        batch_id=batch_id,
        filename=summary.filename,
        status="running",
        total_records=len(importable),
    )
    import_store[batch_id] = status

    if not importable:
        status.status = "failed"
        status.errors.append({"code": "no_importable_records", "message": "沒有可匯入資料"})
        return status

    success, failed, errors = import_books(
        importable,
        duplicate_policy=request.duplicate_policy,
        batch_size=request.batch_size or IMPORT_BATCH_SIZE,
    )
    status.processed_records = success + failed
    status.success_records = success
    status.failed_records = failed
    status.errors = errors
    status.status = "completed" if failed == 0 else "failed"
    return status


@app.get("/api/import/{batch_id}", response_model=ImportStatus)
def import_status(batch_id: str) -> ImportStatus:
    status = import_store.get(batch_id)
    if status is None:
        raise HTTPException(status_code=404, detail="找不到 batch_id")
    return status

@app.get("/")
async def root():
    return {
        "success": True,
        "service": "Books Vector API",
        "status": "running",
        "health": "/api/health",
        "docs": "/docs"
    }