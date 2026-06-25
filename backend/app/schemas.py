from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.config import DEFAULT_CANDIDATE_LIMIT, DEFAULT_LLM_MIN_SCORE, DEFAULT_TOP_K


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


class SearchFilters(BaseModel):
    language: str | None = None
    publisher: str | None = None
    subjects: list[str] | None = None
    publish_year_from: int | None = None
    publish_year_to: int | None = None


class BookSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=50)
    candidate_limit: int = Field(default=DEFAULT_CANDIDATE_LIMIT, ge=5, le=100)
    score_threshold: float | None = Field(default=None, ge=0, le=1)
    llm_min_score: float = Field(default=DEFAULT_LLM_MIN_SCORE, ge=0, le=1)
    use_llm_rerank: bool = True
    include_details: bool = False
    filters: SearchFilters | None = None

    @model_validator(mode="after")
    def candidate_limit_must_cover_top_k(self) -> "BookSearchRequest":
        if self.candidate_limit < self.top_k:
            raise ValueError("candidate_limit must be greater than or equal to top_k")
        return self


class BookSearchResult(BaseModel):
    isbn: str
    title: str | None = None
    authors: list[str] | str | None = None
    publisher: str | None = None
    publish_date: str | int | float | None = None
    language: str | None = None
    subjects: list[str] | str | None = None
    description: str | None = None
    vector_score: float
    llm_score: float | None = None
    final_score: float
    reason: str | None = None
    payload: dict[str, Any] | None = None


class SearchMetadata(BaseModel):
    qdrant_candidates: int
    llm_filtered_candidates: int
    returned_results: int
    llm_rerank_used: bool
    elapsed_ms: int
    fallback_reason: str | None = None
    vector_elapsed_ms: int | None = None
    llm_elapsed_ms: int | None = None


class BookSearchResponse(BaseModel):
    success: bool = True
    request_id: str
    query: str
    count: int
    isbns: list[str]
    results: list[BookSearchResult] | None = None
    metadata: SearchMetadata


class ServiceHealth(BaseModel):
    status: str
    model: str | None = None
    container: str | None = None
    collection: str | None = None
    detail: str | None = None


class BookSearchHealthResponse(BaseModel):
    success: bool
    services: dict[str, ServiceHealth]


class LlmSelectedCandidate(BaseModel):
    candidate_id: str
    score: float = Field(ge=0, le=1)
    reason: str = Field(max_length=100)


class LlmRerankResponse(BaseModel):
    selected: list[LlmSelectedCandidate] = Field(default_factory=list)
