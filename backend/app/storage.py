from typing import Any

from app.schemas import ImportStatus, ValidationSummary


validation_store: dict[str, dict[str, Any]] = {}
import_store: dict[str, ImportStatus] = {}
