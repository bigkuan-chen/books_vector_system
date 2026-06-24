import json
import re
import uuid
from collections import Counter
from typing import Any

from app.config import MAX_JSON_DEPTH, MAX_RECORDS, MAX_UPLOAD_SIZE_MB
from app.schemas import RecordPreview, ValidationMessage, ValidationSummary


ISBN_ALIASES = ("isbn", "ISBN", "_ISBN標準化", "_ISBN", "_ISBN資料", "_ISBN璅")
TITLE_ALIASES = ("書名", "申請書名", "title", "Title", "題名", "名稱", "?唾??詨?")
AUTHOR_ALIASES = ("作者", "author", "authors", "Author", "著者", "雿")
PUBLISHER_ALIASES = ("出版機構", "出版社", "publisher", "Publisher")
SUBJECT_ALIASES = ("圖書主題", "標題", "建議上架分類", "subjects", "subject", "categories", "分類", "主題")
DESCRIPTION_ALIASES = ("description", "summary", "內容簡介", "簡介")


def normalize_isbn(value: Any) -> str:
    return re.sub(r"[-\s]", "", str(value).strip())


def _message(severity: str, code: str, message: str) -> ValidationMessage:
    return ValidationMessage(severity=severity, code=code, message=message)


def _json_depth(value: Any, current: int = 0) -> int:
    if isinstance(value, dict):
        if not value:
            return current + 1
        return max(_json_depth(item, current + 1) for item in value.values())
    if isinstance(value, list):
        if not value:
            return current + 1
        return max(_json_depth(item, current + 1) for item in value)
    return current


def find_field(record: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    lower_map = {key.lower(): key for key in record.keys()}
    for alias in aliases:
        if alias in record:
            return record[alias]
        found_key = lower_map.get(alias.lower())
        if found_key is not None:
            return record[found_key]
    return None


def list_field(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def text_field(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalized_book(record: dict[str, Any], row_index: int, filename: str, batch_id: str) -> dict[str, Any]:
    isbn = normalize_isbn(find_field(record, ISBN_ALIASES))
    title = text_field(find_field(record, TITLE_ALIASES))
    authors = list_field(find_field(record, AUTHOR_ALIASES))
    publisher = text_field(find_field(record, PUBLISHER_ALIASES))
    subjects = list_field(find_field(record, SUBJECT_ALIASES))
    description = find_field(record, DESCRIPTION_ALIASES)
    if description is not None:
        description = str(description)

    return {
        "isbn": isbn,
        "title": title,
        "authors": authors,
        "publisher": publisher,
        "subjects": subjects,
        "description": description,
        "source_filename": filename,
        "source_record_index": row_index,
        "import_batch_id": batch_id,
    }


def parse_uploaded_json(content: bytes, filename: str) -> tuple[list[dict[str, Any]], list[ValidationMessage]]:
    messages: list[ValidationMessage] = []
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        return [], [_message("error", "file_too_large", f"檔案超過 {MAX_UPLOAD_SIZE_MB} MB 限制")]

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [], [_message("error", "invalid_encoding", f"檔案必須是 UTF-8：{exc}")]

    try:
        root = json.loads(text)
    except json.JSONDecodeError as exc:
        return [], [_message("error", "invalid_json", f"JSON 格式錯誤：第 {exc.lineno} 行第 {exc.colno} 欄，{exc.msg}")]

    if _json_depth(root) > MAX_JSON_DEPTH:
        return [], [_message("error", "json_too_deep", f"JSON 巢狀層數超過 {MAX_JSON_DEPTH}")]

    if isinstance(root, list):
        records = root
    elif isinstance(root, dict):
        books = root.get("books")
        if not isinstance(books, list):
            return [], [_message("error", "books_is_not_array", "JSON 物件格式必須包含 books 陣列")]
        records = books
    else:
        return [], [_message("error", "root_is_not_array", "JSON 根節點必須是陣列或包含 books 陣列的物件")]

    if len(records) > MAX_RECORDS:
        return [], [_message("error", "too_many_records", f"資料筆數超過 {MAX_RECORDS} 筆限制")]

    object_records: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if isinstance(record, dict):
            object_records.append(record)
        else:
            object_records.append({"__invalid_record__": record})

    return object_records, messages


def validate_records(records: list[dict[str, Any]], filename: str) -> tuple[ValidationSummary, list[dict[str, Any]]]:
    validation_id = str(uuid.uuid4())
    batch_id = str(uuid.uuid4())
    normalized_records: list[dict[str, Any]] = []
    previews: list[RecordPreview] = []
    normalized_isbns = [
        normalize_isbn(find_field(record, ISBN_ALIASES))
        for record in records
        if find_field(record, ISBN_ALIASES) is not None
    ]
    isbn_counts = Counter(isbn for isbn in normalized_isbns if isbn)
    duplicate_records = 0

    for row_index, record in enumerate(records, start=1):
        messages: list[ValidationMessage] = []
        isbn_raw = find_field(record, ISBN_ALIASES)
        title_raw = find_field(record, TITLE_ALIASES)
        author_raw = find_field(record, AUTHOR_ALIASES)
        publisher_raw = find_field(record, PUBLISHER_ALIASES)
        isbn = normalize_isbn(isbn_raw) if isbn_raw is not None else ""
        title = text_field(title_raw)
        authors = list_field(author_raw)
        publisher = text_field(publisher_raw)

        if "__invalid_record__" in record:
            messages.append(_message("error", "record_is_not_object", "這筆資料不是 JSON 物件"))
        if isbn_raw is None:
            messages.append(_message("error", "missing_isbn", "缺少 ISBN 欄位"))
        elif not isbn:
            messages.append(_message("error", "blank_isbn", "ISBN 不可空白"))
        elif str(isbn_raw).strip() != isbn:
            messages.append(_message("info", "isbn_normalized", "ISBN 已移除空白或連字號"))

        if title_raw is None:
            messages.append(_message("error", "missing_title", "缺少書名或申請書名欄位"))
        elif not title:
            messages.append(_message("error", "blank_title", "書名或申請書名不可空白"))

        if author_raw is None:
            messages.append(_message("error", "missing_author", "缺少作者欄位"))
        elif not authors:
            messages.append(_message("error", "blank_author", "作者不可空白"))

        if publisher_raw is None:
            messages.append(_message("error", "missing_publisher", "缺少出版機構欄位"))
        elif not publisher:
            messages.append(_message("error", "blank_publisher", "出版機構不可空白"))

        if isbn and isbn_counts[isbn] > 1:
            duplicate_records += 1
            messages.append(_message("warning", "duplicate_isbn_in_file", "檔案內有重複 ISBN，匯入時會依策略處理"))

        has_error = any(message.severity == "error" for message in messages)
        has_warning = any(message.severity == "warning" for message in messages)
        status = "error" if has_error else "warning" if has_warning else "valid"

        normalized = normalized_book(record, row_index, filename, batch_id)
        normalized["is_valid"] = not has_error
        normalized["messages"] = [message.model_dump() for message in messages]
        normalized["source_data"] = record
        normalized_records.append(normalized)

        previews.append(
            RecordPreview(
                row_number=row_index,
                isbn=isbn or None,
                title=title or None,
                status=status,
                messages=messages,
            )
        )

    valid_records = sum(1 for preview in previews if preview.status == "valid")
    warning_records = sum(1 for preview in previews if preview.status == "warning")
    invalid_records = sum(1 for preview in previews if preview.status == "error")
    summary = ValidationSummary(
        validation_id=validation_id,
        filename=filename,
        total_records=len(records),
        valid_records=valid_records,
        warning_records=warning_records,
        invalid_records=invalid_records,
        duplicate_records=duplicate_records,
        importable=(valid_records + warning_records) > 0,
        preview=previews[:200],
    )
    return summary, normalized_records
