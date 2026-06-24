from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import IMPORT_BATCH_SIZE, QDRANT_COLLECTION, QDRANT_URL
from app.qdrant_service import collection_health, import_books
from app.schemas import HealthResponse, ImportExecuteRequest, ImportStatus, ValidationSummary
from app.storage import import_store, validation_store
from app.validation import parse_uploaded_json, validate_records


app = FastAPI(title="Book Vector Database Importer", version="MVP-v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
