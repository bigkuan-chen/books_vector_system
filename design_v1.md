project:
  name: "Book Vector Database Importer"
  display_name: "圖書向量資料庫匯入系統"
  version: "MVP-v1"
  phase: 1
  language: "zh-TW"

goal:
  description: >
    建立一個網頁系統，讓使用者選擇圖書 JSON 檔案，
    驗證 JSON 格式及必要欄位，將有效圖書資料轉換為向量，
    並匯入本機 Qdrant。
  critical_requirement:
    - "每筆圖書原始 JSON 必須完整保存於 Qdrant payload.source_data"
    - "不得因為系統未定義欄位而刪除原始 JSON 欄位"
    - "匯入前必須先完成檔案與資料驗證"
    - "錯誤資料不得送入 embedding model"
    - "重複 ISBN 使用 upsert 更新"

technology:
  frontend:
    framework: "Next.js"
    language: "TypeScript"
    ui: "Tailwind CSS"

  backend:
    framework: "FastAPI"
    language: "Python"
    validation: "Pydantic"

  vector_database:
    product: "Qdrant"
    deployment: "Docker"
    container_name: "my_qdrant"
    url: "http://localhost:6333"
    collection_name: "books"

  embedding:
    library: "sentence-transformers"
    model: "intfloat/multilingual-e5-small"
    distance: "Cosine"
    device: "cpu"

input:
  accepted_file_types:
    - ".json"

  accepted_root_formats:
    array:
      example: "[{...}, {...}]"

    object_with_books:
      example:
        books:
          - "{...}"

  encoding:
    preferred: "UTF-8"
    reject_invalid_encoding: true

  limits:
    max_file_size_mb: 100
    max_records: 100000

book_validation:
  required_fields:
    isbn:
      type:
        - "string"
        - "number"
      allow_blank: false
      normalization:
        - "convert_to_string"
        - "trim"
        - "remove_hyphen"
        - "remove_spaces"

    title:
      type:
        - "string"
      allow_blank: false
      normalization:
        - "trim"

  optional_fields:
    author:
      accepted_types:
        - "string"
        - "array"
      normalization:
        string_to_array: true

    subjects:
      accepted_types:
        - "string"
        - "array"
      normalization:
        string_to_array: true

    description:
      accepted_types:
        - "string"
        - "null"

    publish_date:
      accepted_types:
        - "string"
        - "number"
        - "null"
      storage_policy: "preserve_original_value"

  unknown_fields:
    allowed: true
    preserve: true
    destination: "payload.source_data"

validation_levels:
  error:
    importable: false
    examples:
      - "invalid_json"
      - "root_is_not_array"
      - "books_is_not_array"
      - "record_is_not_object"
      - "missing_isbn"
      - "blank_isbn"
      - "missing_title"
      - "blank_title"

  warning:
    importable: true
    examples:
      - "missing_author"
      - "missing_description"
      - "missing_subjects"
      - "duplicate_isbn_in_file"

  info:
    importable: true
    examples:
      - "author_string_converted_to_array"
      - "isbn_hyphen_removed"

embedding:
  fields:
    - "title"
    - "subtitle"
    - "author"
    - "subjects"
    - "keywords"
    - "description"
    - "summary"
    - "table_of_contents"

  template: |
    書名：{title}
    副書名：{subtitle}
    作者：{authors}
    出版社：{publisher}
    主題：{subjects}
    關鍵字：{keywords}
    內容簡介：{description}
    目次：{table_of_contents}

  empty_field_policy: "skip"
  max_text_length: 12000

qdrant_point:
  id:
    strategy: "uuid5"
    namespace: "URL"
    source: "book:{normalized_isbn}"

  vector:
    source: "embedding_text"
    distance: "Cosine"

  payload:
    normalized_fields:
      - "isbn"
      - "title"
      - "authors"
      - "publisher"
      - "language"
      - "subjects"
      - "description"

    embedding_text:
      enabled: true

    source_data:
      description: "完整原始 JSON 物件"
      preserve_all_fields: true
      allow_nested_objects: true
      allow_arrays: true

    metadata:
      fields:
        - "source_filename"
        - "source_record_index"
        - "import_batch_id"
        - "imported_at"
        - "schema_version"

import:
  collection:
    auto_create: true
    name: "books"

  mode:
    default: "valid_only"
    options:
      valid_only:
        description: "只匯入驗證成功的資料"

      all_or_nothing:
        description: "檔案中只要有一筆錯誤，就停止整批匯入"

  duplicate_policy:
    default: "upsert"
    options:
      - "upsert"
      - "skip"
      - "reject"

  batch:
    default_size: 100
    min_size: 10
    max_size: 1000

  retry:
    enabled: true
    max_attempts: 3

  transaction_log:
    enabled: true
    fields:
      - "batch_id"
      - "filename"
      - "started_at"
      - "completed_at"
      - "total_records"
      - "success_records"
      - "failed_records"
      - "errors"

api:
  base_path: "/api"

  endpoints:
    qdrant_health:
      method: "GET"
      path: "/health/qdrant"

    validate_file:
      method: "POST"
      path: "/import/validate"
      content_type: "multipart/form-data"

    execute_import:
      method: "POST"
      path: "/import/execute"

    import_status:
      method: "GET"
      path: "/import/{batch_id}"

    validation_errors:
      method: "GET"
      path: "/validation/{validation_id}/errors"

ui:
  page:
    title: "圖書向量資料匯入"

  sections:
    connection_status:
      fields:
        - "qdrant_status"
        - "qdrant_url"
        - "collection_name"
        - "collection_status"

    file_selection:
      components:
        - "file_picker"
        - "file_name"
        - "file_size"
        - "validate_button"

    validation_summary:
      fields:
        - "total_records"
        - "valid_records"
        - "warning_records"
        - "invalid_records"
        - "duplicate_records"

    record_preview:
      columns:
        - "row_number"
        - "isbn"
        - "title"
        - "status"
        - "messages"

      filters:
        - "all"
        - "valid"
        - "warning"
        - "error"

    import_options:
      fields:
        - "import_mode"
        - "duplicate_policy"
        - "batch_size"

    import_progress:
      fields:
        - "status"
        - "progress_percent"
        - "processed_records"
        - "success_records"
        - "failed_records"

  buttons:
    - id: "select_file"
      label: "選擇 JSON 檔案"

    - id: "validate"
      label: "載入並檢查"

    - id: "import"
      label: "匯入向量資料庫"
      enabled_when:
        - "validation_completed"
        - "valid_records_greater_than_zero"

security:
  file:
    never_execute_uploaded_content: true
    randomize_temporary_filename: true
    delete_temporary_file_after_import: true

  json:
    reject_non_json_content: true
    max_nested_depth: 20

  logging:
    exclude_embedding_vector: true
    mask_sensitive_fields:
      - "api_key"
      - "password"

environment:
  variables:
    APP_ENV: "development"
    QDRANT_URL: "http://localhost:6333"
    QDRANT_API_KEY: ""
    QDRANT_COLLECTION: "books"
    EMBEDDING_MODEL: "intfloat/multilingual-e5-small"
    EMBEDDING_DEVICE: "cpu"
    IMPORT_BATCH_SIZE: "100"
    MAX_UPLOAD_SIZE_MB: "100"

acceptance_criteria:
  - id: "AC-001"
    description: "使用者可以從瀏覽器選擇 JSON 檔案"

  - id: "AC-002"
    description: "系統可以識別 JSON 語法錯誤"

  - id: "AC-003"
    description: "系統可以顯示缺少 ISBN 或 title 的資料"

  - id: "AC-004"
    description: "匯入按鈕只能在驗證完成後使用"

  - id: "AC-005"
    description: "有效資料會產生 embedding vector"

  - id: "AC-006"
    description: "資料會匯入本機 Qdrant books collection"

  - id: "AC-007"
    description: "原始圖書 JSON 完整存在 payload.source_data"

  - id: "AC-008"
    description: "原始 JSON 的未知欄位不得遺失"

  - id: "AC-009"
    description: "相同 ISBN 再次匯入時使用固定 Point ID 更新資料"

  - id: "AC-010"
    description: "匯入完成後顯示成功、失敗及總筆數"