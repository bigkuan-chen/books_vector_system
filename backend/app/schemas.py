from typing import Any, Literal

from pydantic import BaseModel, Field


Severity = Literal["error", "warning", "info"]
RecordStatus = Literal["valid", "warning", "error"]


class ValidationMessage(BaseModel):
    severity: Severity
    code: str
    message: str


class RecordPreview(BaseModel):
    row_number: int
    isbn: str | None = None
    title: str | None = None
    status: RecordStatus
    messages: list[ValidationMessage] = Field(default_factory=list)


class ValidationSummary(BaseModel):
    validation_id: str
    filename: str
    total_records: int
    valid_records: int
    warning_records: int
    invalid_records: int
    duplicate_records: int
    importable: bool
    messages: list[ValidationMessage] = Field(default_factory=list)
    preview: list[RecordPreview] = Field(default_factory=list)


class ImportExecuteRequest(BaseModel):
    validation_id: str
    import_mode: Literal["valid_only", "all_or_nothing"] = "valid_only"
    duplicate_policy: Literal["upsert", "skip", "reject"] = "upsert"
    batch_size: int = Field(default=100, ge=10, le=1000)


class ImportStatus(BaseModel):
    batch_id: str
    filename: str
    status: Literal["pending", "running", "completed", "failed"]
    total_records: int
    processed_records: int = 0
    success_records: int = 0
    failed_records: int = 0
    errors: list[dict[str, Any]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    qdrant_status: Literal["ok", "error"]
    qdrant_url: str
    collection_name: str
    collection_status: str
    dashboard_url: str | None = None
    available_collections: list[str] = Field(default_factory=list)
    detail: str | None = None
    error_type: str | None = None
    error_traceback: str | None = None
