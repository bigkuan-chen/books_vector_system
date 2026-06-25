```yaml
project:
  name: "Book Vector Database Query System"
  display_name: "圖書向量資料庫自然語言查詢系統"
  version: "MVP-v2"
  language: "zh-TW"

  description: >
    提供 RESTful API 接收使用者的自然語言圖書查詢條件，
    使用與圖書匯入階段相同的 Embedding Model，
    將查詢文字轉換為向量後搜尋 Qdrant books collection。
    取得初步候選圖書後，再交由 LLM 進行語意過濾與重新排序，
    最後從符合條件圖書的 payload 中取出 ISBN，
    並以 JSON 格式回傳。

goals:
  primary:
    - "使用自然語言查詢圖書資料"
    - "將自然語言查詢轉換為向量"
    - "搜尋本機 Qdrant books collection"
    - "使用 LLM 過濾不符合查詢意圖的候選圖書"
    - "使用 LLM 對候選圖書進行重新排序"
    - "從 payload 取出 ISBN"
    - "透過 RESTful API 回傳 ISBN JSON"

  critical_requirements:
    - "查詢與匯入必須使用相同的 Embedding Model"
    - "Qdrant 搜尋結果必須保留 payload"
    - "ISBN 必須從 Qdrant payload 取得"
    - "LLM 不可自行產生不存在於候選資料中的 ISBN"
    - "最終 ISBN 必須存在於 Qdrant 搜尋候選資料中"
    - "LLM 回傳資料必須經過後端程式驗證"
    - "查詢失敗時必須回傳標準錯誤 JSON"
    - "不得將完整向量內容寫入應用程式 log"

system_architecture:
  components:
    - id: "C01"
      name: "API Client"
      description: >
        第三方圖書館系統、前端網站、Postman 或其他服務，
        透過 HTTP RESTful API 傳送自然語言查詢。

    - id: "C02"
      name: "FastAPI Query API"
      technology:
        framework: "FastAPI"
        language: "Python"
      responsibilities:
        - "接收查詢 Request"
        - "驗證輸入參數"
        - "產生 request_id"
        - "控制完整查詢流程"
        - "組合並回傳結果"

    - id: "C03"
      name: "Query Preprocessor"
      responsibilities:
        - "去除查詢前後空白"
        - "限制查詢長度"
        - "標準化換行及特殊字元"
        - "判斷查詢是否為空"
        - "建立查詢 embedding text"

    - id: "C04"
      name: "Embedding Service"
      technology:
        library: "sentence-transformers"
        model: "intfloat/multilingual-e5-small"
      responsibilities:
        - "將自然語言查詢轉換為向量"
        - "確保模型與圖書匯入階段相同"
        - "執行向量正規化"

    - id: "C05"
      name: "Qdrant Search Service"
      technology:
        database: "Qdrant"
        container_name: "books_container"
        collection_name: "books"
      responsibilities:
        - "使用查詢向量搜尋 books collection"
        - "取得候選圖書"
        - "取得相似度分數"
        - "取得完整 payload"
        - "套用 metadata filter"

    - id: "C06"
      name: "Candidate Data Builder"
      responsibilities:
        - "整理 Qdrant 候選圖書"
        - "從 payload 取出圖書欄位"
        - "限制送給 LLM 的文字長度"
        - "保留 point_id、isbn 與 vector_score"
        - "產生候選資料編號 candidate_id"

    - id: "C07"
      name: "LLM Reranker"
      responsibilities:
        - "理解使用者查詢意圖"
        - "比較候選圖書與查詢條件"
        - "排除不符合的候選圖書"
        - "計算語意符合分數"
        - "重新排序候選圖書"
        - "輸出結構化 JSON"

    - id: "C08"
      name: "Result Validator"
      responsibilities:
        - "驗證 LLM JSON 格式"
        - "驗證 candidate_id 存在於候選清單"
        - "驗證 ISBN 來自 Qdrant payload"
        - "移除重複 ISBN"
        - "限制最大回傳筆數"
        - "依 final_score 排序"

    - id: "C09"
      name: "RESTful JSON Response"
      responsibilities:
        - "回傳符合條件的 ISBN"
        - "回傳查詢統計資訊"
        - "回傳標準錯誤格式"

data_flow:
  steps:
    - step: 1
      component: "C01"
      action: >
        Client 呼叫 POST /api/v1/books/search，
        傳入自然語言查詢條件。

    - step: 2
      component: "C02"
      action: >
        FastAPI 驗證 query、top_k、candidate_limit、
        score_threshold 與 filters。

    - step: 3
      component: "C03"
      action: >
        將自然語言查詢標準化，
        並依 Embedding Model 規則建立 query_text。

    - step: 4
      component: "C04"
      action: >
        使用與圖書匯入相同的 Embedding Model，
        將 query_text 轉換為 query_vector。

    - step: 5
      component: "C05"
      action: >
        使用 query_vector 搜尋 Qdrant books collection，
        取得 candidate_limit 筆候選圖書及完整 payload。

    - step: 6
      component: "C06"
      action: >
        將候選圖書轉換為適合 LLM 比較的結構，
        每筆候選資料分配唯一 candidate_id。

    - step: 7
      component: "C07"
      action: >
        將原始查詢與候選圖書送入 LLM，
        執行過濾、評分及重新排序。

    - step: 8
      component: "C08"
      action: >
        驗證 LLM 回傳結果，
        僅保留原始 Qdrant 候選清單中的 candidate_id 與 ISBN。

    - step: 9
      component: "C09"
      action: >
        從驗證後結果取出 ISBN，
        以標準 JSON 格式回傳給 Client。

technology:
  backend:
    language: "Python"
    version: "3.11+"
    framework: "FastAPI"
    server: "Uvicorn"
    validation: "Pydantic"

  vector_database:
    product: "Qdrant"
    deployment: "Docker"
    container_name: "books_container"
    url: "http://books_container:6333"
    local_url: "http://localhost:6333"
    collection_name: "books"
    distance_metric: "Cosine"

  embedding:
    provider: "sentence-transformers"
    model: "intfloat/multilingual-e5-small"
    device: "cpu"
    normalize_embeddings: true

  llm:
    provider: "configurable"
    supported_providers:
      - "Google Gemini"
    model : "gemini-3-flash-preview"
    response_format: "JSON"
    temperature: 0
    purpose:
      - "candidate_filtering"
      - "semantic_reranking"

api:
  base_path: "/api/v1"

  endpoints:
    - id: "API-001"
      name: "Natural Language Book Search"
      method: "POST"
      path: "/books/search"
      content_type: "application/json"
      description: >
        接收自然語言圖書查詢條件，
        搜尋 Qdrant 並使用 LLM 過濾與重新排序，
        最後回傳符合條件的 ISBN。

      request_schema:
        type: "object"

        required:
          - "query"

        properties:
          query:
            type: "string"
            description: "自然語言圖書查詢條件"
            min_length: 1
            max_length: 2000
            example: >
              查詢適合初學者閱讀的 Python 機器學習中文書籍，
              希望內容包含資料分析與實作範例。

          top_k:
            type: "integer"
            description: "最終最多回傳的 ISBN 數量"
            default: 10
            minimum: 1
            maximum: 50

          candidate_limit:
            type: "integer"
            description: "從 Qdrant 取得並送給 LLM 比較的候選數量"
            default: 30
            minimum: 5
            maximum: 100

          score_threshold:
            type:
              - "number"
              - "null"
            description: "Qdrant 最低向量相似度門檻"
            default: null
            minimum: 0
            maximum: 1

          llm_min_score:
            type: "number"
            description: "LLM 判斷符合查詢意圖的最低分數"
            default: 0.6
            minimum: 0
            maximum: 1

          use_llm_rerank:
            type: "boolean"
            description: "是否啟用 LLM 過濾與重新排序"
            default: true

          include_details:
            type: "boolean"
            description: >
              false 時只回傳 ISBN；
              true 時附帶書名及評分等資訊。
            default: false

          filters:
            type:
              - "object"
              - "null"
            description: "Qdrant payload metadata 過濾條件"
            properties:
              language:
                type:
                  - "string"
                  - "null"
                example: "zh-TW"

              publisher:
                type:
                  - "string"
                  - "null"

              subjects:
                type:
                  - "array"
                  - "null"
                items:
                  type: "string"

              publish_year_from:
                type:
                  - "integer"
                  - "null"

              publish_year_to:
                type:
                  - "integer"
                  - "null"

      request_example:
        query: >
          找適合 Python 初學者的資料分析書籍，
          希望包含 pandas、資料視覺化及實作案例，
          以繁體中文書籍優先。
        top_k: 5
        candidate_limit: 30
        score_threshold: 0.35
        llm_min_score: 0.65
        use_llm_rerank: true
        include_details: false
        filters:
          language: "zh-TW"
          subjects:
            - "Python"
            - "資料分析"
          publish_year_from: 2020
          publish_year_to: null

      response_schema:
        type: "object"
        required:
          - "success"
          - "request_id"
          - "query"
          - "count"
          - "isbns"

        properties:
          success:
            type: "boolean"

          request_id:
            type: "string"

          query:
            type: "string"

          count:
            type: "integer"

          isbns:
            type: "array"
            items:
              type: "string"

          results:
            type: "array"
            description: "include_details=true 時回傳"
            items:
              type: "object"
              properties:
                isbn:
                  type: "string"
                title:
                  type: "string"
                vector_score:
                  type: "number"
                llm_score:
                  type: "number"
                final_score:
                  type: "number"
                reason:
                  type: "string"

          metadata:
            type: "object"
            properties:
              qdrant_candidates:
                type: "integer"
              llm_filtered_candidates:
                type: "integer"
              returned_results:
                type: "integer"
              llm_rerank_used:
                type: "boolean"
              elapsed_ms:
                type: "integer"

      response_example:
        success: true
        request_id: "req_20260625_001"
        query: >
          找適合 Python 初學者的資料分析書籍，
          希望包含 pandas、資料視覺化及實作案例，
          以繁體中文書籍優先。
        count: 3
        isbns:
          - "9789861234567"
          - "9789577654321"
          - "9786269876543"
        metadata:
          qdrant_candidates: 30
          llm_filtered_candidates: 7
          returned_results: 3
          llm_rerank_used: true
          elapsed_ms: 865

    - id: "API-002"
      name: "Book Search Health Check"
      method: "GET"
      path: "/health"
      description: "檢查 API、Embedding Model、Qdrant 及 LLM 狀態"

      response_example:
        success: true
        services:
          api:
            status: "healthy"
          embedding:
            status: "healthy"
            model: "intfloat/multilingual-e5-small"
          qdrant:
            status: "healthy"
            container: "books_container"
            collection: "books"
          llm:
            status: "healthy"

query_processing:
  validation:
    query:
      required: true
      trim: true
      reject_blank: true
      min_length: 1
      max_length: 2000

    top_k:
      default: 10
      min: 1
      max: 50

    candidate_limit:
      default: 30
      min: 5
      max: 100
      rule: "candidate_limit 必須大於或等於 top_k"

  normalization:
    - "trim_leading_and_trailing_spaces"
    - "normalize_newline"
    - "remove_control_characters"
    - "preserve_original_language"

  embedding_text:
    strategy: "query_prefix"

    template: |
      query: {query}

    notes:
      - "使用 E5 系列模型時，查詢文字使用 query: 前綴"
      - "匯入圖書文字建議使用 passage: 前綴"
      - "查詢與匯入必須使用同一個模型及相同向量維度"

qdrant_search:
  connection:
    url_env: "QDRANT_URL"
    collection_env: "QDRANT_COLLECTION"
    default_url: "http://books_container:6333"
    default_collection: "books"

  query:
    vector_name: null
    with_payload: true
    with_vector: false
    default_limit: 30
    default_score_threshold: null

  expected_payload:
    isbn_paths:
      - "isbn"
      - "source_data.isbn"

    fields:
      isbn:
        required: true
        lookup_priority:
          - "payload.isbn"
          - "payload.source_data.isbn"

      title:
        required_for_llm: true
        lookup_priority:
          - "payload.title"
          - "payload.source_data.title"

      authors:
        required_for_llm: false
        lookup_priority:
          - "payload.authors"
          - "payload.author"
          - "payload.source_data.author"

      publisher:
        required_for_llm: false
        lookup_priority:
          - "payload.publisher"
          - "payload.source_data.publisher"

      subjects:
        required_for_llm: false
        lookup_priority:
          - "payload.subjects"
          - "payload.source_data.subjects"

      description:
        required_for_llm: false
        lookup_priority:
          - "payload.description"
          - "payload.source_data.description"
          - "payload.source_data.summary"

      publish_date:
        required_for_llm: false
        lookup_priority:
          - "payload.publish_date"
          - "payload.source_data.publish_date"

      language:
        required_for_llm: false
        lookup_priority:
          - "payload.language"
          - "payload.source_data.language"

  metadata_filters:
    enabled: true

    supported:
      language:
        payload_path: "language"
        operator: "match"

      publisher:
        payload_path: "publisher"
        operator: "match"

      subjects:
        payload_path: "subjects"
        operator: "match_any"

      publish_year_from:
        payload_path: "publish_year"
        operator: "gte"

      publish_year_to:
        payload_path: "publish_year"
        operator: "lte"

  invalid_candidate_policy:
    missing_isbn: "exclude"
    missing_title: "allow_with_warning"
    invalid_payload: "exclude"

candidate_builder:
  candidate_id:
    strategy: "sequential"
    format: "C{number}"

  fields_sent_to_llm:
    - "candidate_id"
    - "isbn"
    - "title"
    - "authors"
    - "publisher"
    - "publish_date"
    - "language"
    - "subjects"
    - "description"
    - "vector_score"

  limits:
    max_candidates: 100
    max_title_chars: 500
    max_description_chars: 2000
    max_subjects: 30
    max_authors: 20
    max_total_prompt_chars: 60000

  example:
    candidate_id: "C01"
    isbn: "9789861234567"
    title: "Python 資料分析實戰"
    authors:
      - "王大明"
    publisher: "科技出版社"
    publish_date: "2025-01-15"
    language: "zh-TW"
    subjects:
      - "Python"
      - "pandas"
      - "資料分析"
    description: "介紹 pandas、NumPy 與資料視覺化實作。"
    vector_score: 0.8215

llm_reranking:
  enabled: true

  purpose:
    - "理解複合式自然語言條件"
    - "排除僅有部分關鍵字相似但實際內容不符的圖書"
    - "依照使用者真正意圖重新排序"
    - "產生簡短的符合理由"

  configuration:
    provider_env: "LLM_PROVIDER"
    model_env: "LLM_MODEL"
    api_base_env: "LLM_API_BASE"
    api_key_env: "LLM_API_KEY"
    temperature: 0
    timeout_seconds: 30
    max_retries: 2
    response_format: "json_object"

  scoring:
    range:
      min: 0
      max: 1

    dimensions:
      semantic_relevance:
        weight: 0.45
        description: "圖書主題與查詢語意的符合程度"

      requirement_coverage:
        weight: 0.30
        description: "符合使用者明確條件的完整程度"

      audience_fit:
        weight: 0.15
        description: "是否符合初學者、進階者或指定讀者"

      metadata_fit:
        weight: 0.10
        description: "語言、出版年代、主題等 metadata 符合程度"

  system_prompt: |
    你是一個圖書資料檢索重新排序器。

    你的任務是根據使用者的自然語言查詢，
    評估每一本候選圖書是否符合查詢條件。

    嚴格規則：

    1. 只能選擇候選清單中存在的 candidate_id。
    2. 不可自行新增圖書、ISBN 或候選資料。
    3. ISBN 僅供識別，不可修改。
    4. 必須根據候選圖書提供的書名、作者、主題、
       出版資訊與內容簡介進行判斷。
    5. 若資料不足以確認符合條件，應降低分數，
       不可自行推測缺少的內容。
    6. score 範圍必須介於 0 到 1。
    7. 只回傳合法 JSON，不可回傳 Markdown。
    8. selected 必須依 score 由高至低排序。
    9. reason 使用繁體中文，最多 100 個字。
    10. 不符合查詢的候選圖書不要放入 selected。

  user_prompt_template: |
    使用者查詢：

    {query}

    最低符合分數：

    {llm_min_score}

    候選圖書：

    {candidates_json}

    請過濾並重新排序候選圖書。

    回傳格式：

    {
      "selected": [
        {
          "candidate_id": "C01",
          "score": 0.92,
          "reason": "符合 Python 初學、pandas 與資料視覺化需求"
        }
      ]
    }

  expected_response_schema:
    type: "object"
    required:
      - "selected"

    properties:
      selected:
        type: "array"
        items:
          type: "object"
          required:
            - "candidate_id"
            - "score"
            - "reason"
          properties:
            candidate_id:
              type: "string"
            score:
              type: "number"
              minimum: 0
              maximum: 1
            reason:
              type: "string"
              max_length: 100

  invalid_response_policy:
    malformed_json: "fallback_to_vector_results"
    unknown_candidate_id: "remove_item"
    duplicate_candidate_id: "keep_highest_score"
    missing_score: "remove_item"
    score_out_of_range: "clamp_to_0_1"
    timeout: "fallback_to_vector_results"
    provider_error: "fallback_to_vector_results"

result_ranking:
  when_llm_enabled:
    final_score_formula:
      vector_weight: 0.35
      llm_weight: 0.65
      expression: >
        final_score =
        normalized_vector_score * 0.35 +
        llm_score * 0.65

    filtering:
      - "llm_score >= llm_min_score"
      - "candidate_id 必須存在於 Qdrant 候選清單"
      - "ISBN 必須存在於候選 payload"
      - "ISBN 不可為空字串"

    sorting:
      primary: "final_score DESC"
      secondary: "vector_score DESC"

  when_llm_disabled:
    sorting:
      primary: "vector_score DESC"

    filtering:
      - "vector_score >= score_threshold when threshold is provided"

  output:
    limit_source: "top_k"
    remove_duplicate_isbn: true
    isbn_order: "ranking_order"

isbn_extraction:
  source: "Qdrant candidate payload only"

  lookup_priority:
    - "payload.isbn"
    - "payload.source_data.isbn"

  normalization:
    enabled: true
    operations:
      - "convert_to_string"
      - "trim"

  preserve_policy:
    preserve_leading_zero: true
    remove_hyphen: false

  validation:
    reject_empty: true
    strict_isbn_checksum: false

  security_rule: >
    即使 LLM 回傳 ISBN，後端也不可直接採用。
    後端只能依 candidate_id 找回原始 Qdrant 候選資料，
    再從該候選資料的 payload 取出 ISBN。

response_formats:
  isbn_only:
    condition: "include_details = false"

    example:
      success: true
      request_id: "req_20260625_001"
      query: "找適合初學者的 Python 資料分析書籍"
      count: 3
      isbns:
        - "9789861234567"
        - "9789577654321"
        - "9786269876543"
      metadata:
        qdrant_candidates: 30
        llm_filtered_candidates: 6
        returned_results: 3
        llm_rerank_used: true
        elapsed_ms: 865

  with_details:
    condition: "include_details = true"

    example:
      success: true
      request_id: "req_20260625_001"
      query: "找適合初學者的 Python 資料分析書籍"
      count: 2
      isbns:
        - "9789861234567"
        - "9789577654321"
      results:
        - isbn: "9789861234567"
          title: "Python 資料分析實戰"
          vector_score: 0.8215
          llm_score: 0.94
          final_score: 0.8985
          reason: "適合初學者，包含 pandas、視覺化及實作案例"

        - isbn: "9789577654321"
          title: "Python 與 pandas 入門"
          vector_score: 0.7932
          llm_score: 0.88
          final_score: 0.8496
          reason: "涵蓋 Python 與 pandas 基礎，符合入門需求"

      metadata:
        qdrant_candidates: 30
        llm_filtered_candidates: 6
        returned_results: 2
        llm_rerank_used: true
        elapsed_ms: 865

error_handling:
  response_schema:
    success: false
    request_id: "string"
    error:
      code: "string"
      message: "string"
      details: "object or null"

  errors:
    - code: "INVALID_REQUEST"
      http_status: 400
      message: "Request 格式錯誤或缺少必要欄位"

    - code: "EMPTY_QUERY"
      http_status: 400
      message: "查詢條件不可為空"

    - code: "QUERY_TOO_LONG"
      http_status: 400
      message: "查詢文字超過允許長度"

    - code: "INVALID_QUERY_PARAMETER"
      http_status: 422
      message: "查詢參數超出允許範圍"

    - code: "EMBEDDING_SERVICE_ERROR"
      http_status: 503
      message: "查詢向量產生失敗"

    - code: "QDRANT_CONNECTION_ERROR"
      http_status: 503
      message: "無法連接 Qdrant"

    - code: "COLLECTION_NOT_FOUND"
      http_status: 503
      message: "找不到 books collection"

    - code: "QDRANT_SEARCH_ERROR"
      http_status: 500
      message: "Qdrant 搜尋失敗"

    - code: "LLM_SERVICE_ERROR"
      http_status: 503
      message: "LLM 過濾服務失敗"

    - code: "INTERNAL_SERVER_ERROR"
      http_status: 500
      message: "系統內部錯誤"

  no_result:
    http_status: 200

    response:
      success: true
      request_id: "req_20260625_002"
      query: "查詢不存在的特殊主題圖書"
      count: 0
      isbns: []
      metadata:
        qdrant_candidates: 0
        llm_filtered_candidates: 0
        returned_results: 0
        llm_rerank_used: true
        elapsed_ms: 120

fallback_strategy:
  llm_unavailable:
    enabled: true
    behavior: >
      若 LLM 發生 timeout、格式錯誤或服務中斷，
      系統改用 Qdrant vector_score 排序結果。

    response_metadata:
      llm_rerank_used: false
      fallback_reason: "LLM_UNAVAILABLE"

  qdrant_no_result:
    behavior: "直接回傳空 ISBN 陣列，不呼叫 LLM"

  partial_payload_error:
    behavior: >
      排除缺少 ISBN 或 payload 無法解析的候選資料，
      其餘有效資料繼續處理。

performance:
  targets:
    qdrant_candidate_limit_default: 30
    qdrant_candidate_limit_max: 100
    api_timeout_seconds: 45
    embedding_timeout_seconds: 10
    qdrant_timeout_seconds: 10
    llm_timeout_seconds: 30

  optimizations:
    - "Embedding Model 在應用程式啟動時載入一次"
    - "重複查詢可使用查詢向量快取"
    - "只將必要候選欄位傳給 LLM"
    - "限制 description 長度"
    - "LLM temperature 設為 0"
    - "Qdrant 搜尋不回傳 vector"
    - "使用非同步 HTTP Client 呼叫 LLM"
    - "建立 Qdrant payload index 支援 metadata filter"

cache:
  enabled: true
  provider: "memory"
  future_provider: "Redis"

  query_embedding:
    enabled: true
    ttl_seconds: 3600
    key_source:
      - "embedding_model"
      - "normalized_query"

  search_result:
    enabled: false
    ttl_seconds: 300

logging:
  enabled: true
  format: "structured_json"

  fields:
    - "timestamp"
    - "request_id"
    - "endpoint"
    - "query_length"
    - "candidate_limit"
    - "qdrant_candidate_count"
    - "llm_selected_count"
    - "result_count"
    - "elapsed_ms"
    - "status_code"

  excluded_fields:
    - "query_vector"
    - "book_vectors"
    - "llm_api_key"
    - "qdrant_api_key"

  query_content_logging:
    default: false
    reason: "避免自然語言查詢中包含敏感資訊"

security:
  authentication:
    enabled: true
    type: "API Key"
    header: "X-API-Key"
    api_key_env: "BOOK_QUERY_API_KEY"

  rate_limit:
    enabled: true
    requests_per_minute: 60

  input_protection:
    - "限制 query 長度"
    - "移除控制字元"
    - "拒絕空白 query"
    - "限制 candidate_limit"
    - "限制 top_k"
    - "驗證所有 filter 欄位"

  llm_protection:
    - "候選資料視為不可信文字"
    - "LLM 只能輸出 candidate_id"
    - "後端不直接採用 LLM 產生的 ISBN"
    - "LLM 結果必須通過 Pydantic Schema 驗證"
    - "忽略候選圖書內容中的提示指令"
    - "LLM 不可存取 Qdrant 或其他外部工具"

environment:
  file: ".env"

  variables:
    APP_NAME: "Book Vector Query API"
    APP_ENV: "development"
    APP_HOST: "0.0.0.0"
    APP_PORT: "8000"

    BOOK_QUERY_API_KEY: "change-me"

    QDRANT_URL: "http://books_container:6333"
    QDRANT_API_KEY: ""
    QDRANT_COLLECTION: "books"

    EMBEDDING_MODEL: "intfloat/multilingual-e5-small"
    EMBEDDING_DEVICE: "cpu"
    EMBEDDING_NORMALIZE: "true"

    LLM_PROVIDER: "openai-compatible"
    LLM_API_BASE: ""
    LLM_API_KEY: ""
    LLM_MODEL: ""
    LLM_TEMPERATURE: "0"
    LLM_TIMEOUT_SECONDS: "30"

    DEFAULT_TOP_K: "10"
    DEFAULT_CANDIDATE_LIMIT: "30"
    DEFAULT_SCORE_THRESHOLD: ""
    DEFAULT_LLM_MIN_SCORE: "0.60"

    API_TIMEOUT_SECONDS: "45"
    LOG_QUERY_CONTENT: "false"

project_structure:
  root:
    - path: "app/main.py"
      purpose: "FastAPI 啟動點"

    - path: "app/api/routes/book_search.py"
      purpose: "自然語言圖書查詢 RESTful API"

    - path: "app/api/routes/health.py"
      purpose: "服務健康檢查 API"

    - path: "app/core/config.py"
      purpose: "環境設定管理"

    - path: "app/core/security.py"
      purpose: "API Key 驗證與安全設定"

    - path: "app/models/search_request.py"
      purpose: "查詢 Request Pydantic Model"

    - path: "app/models/search_response.py"
      purpose: "查詢 Response Pydantic Model"

    - path: "app/models/llm_response.py"
      purpose: "LLM 結構化輸出驗證"

    - path: "app/services/query_preprocessor.py"
      purpose: "自然語言查詢標準化"

    - path: "app/services/embedding_service.py"
      purpose: "查詢向量產生"

    - path: "app/services/qdrant_service.py"
      purpose: "Qdrant 搜尋與 payload filter"

    - path: "app/services/candidate_builder.py"
      purpose: "建立 LLM 候選資料"

    - path: "app/services/llm_reranker.py"
      purpose: "LLM 過濾及重新排序"

    - path: "app/services/result_validator.py"
      purpose: "驗證 LLM 結果及取得 ISBN"

    - path: "app/services/search_orchestrator.py"
      purpose: "控制完整查詢流程"

    - path: "app/exceptions/handlers.py"
      purpose: "統一錯誤處理"

    - path: "tests/test_book_search.py"
      purpose: "圖書查詢 API 測試"

    - path: "tests/test_result_validator.py"
      purpose: "LLM 結果與 ISBN 安全驗證測試"

    - path: "requirements.txt"
      purpose: "Python 套件"

    - path: "Dockerfile"
      purpose: "Query API Docker Image"

    - path: "docker-compose.yml"
      purpose: "Query API 與 books_container 執行設定"

docker:
  services:
    books_container:
      image: "qdrant/qdrant:latest"
      container_name: "books_container"
      restart: "unless-stopped"

      ports:
        - "6333:6333"
        - "6334:6334"

      volumes:
        - "books_qdrant_storage:/qdrant/storage"

    book_query_api:
      build:
        context: "."
        dockerfile: "Dockerfile"

      container_name: "book_query_api"
      restart: "unless-stopped"

      depends_on:
        - "books_container"

      ports:
        - "8000:8000"

      env_file:
        - ".env"

      environment:
        QDRANT_URL: "http://books_container:6333"
        QDRANT_COLLECTION: "books"

  volumes:
    books_qdrant_storage:

testing:
  unit_tests:
    - id: "UT-001"
      description: "查詢文字可正確標準化"

    - id: "UT-002"
      description: "空白查詢會被拒絕"

    - id: "UT-003"
      description: "candidate_limit 小於 top_k 時會被拒絕"

    - id: "UT-004"
      description: "查詢文字可以產生正確維度的向量"

    - id: "UT-005"
      description: "Qdrant payload 可以正確取出 ISBN"

    - id: "UT-006"
      description: "payload.isbn 不存在時改讀 source_data.isbn"

    - id: "UT-007"
      description: "LLM 回傳未知 candidate_id 時會被移除"

    - id: "UT-008"
      description: "LLM 自行產生的 ISBN 不會被採用"

    - id: "UT-009"
      description: "重複 ISBN 只保留排名最高者"

    - id: "UT-010"
      description: "LLM 服務中斷時改用向量搜尋結果"

  integration_tests:
    - id: "IT-001"
      description: >
        傳入自然語言查詢後，
        可以從 books collection 取得候選圖書。

    - id: "IT-002"
      description: >
        Qdrant 候選圖書可送入 LLM，
        並取得合法 JSON 結果。

    - id: "IT-003"
      description: >
        API 最終回傳的所有 ISBN
        均存在於 Qdrant 候選 payload。

    - id: "IT-004"
      description: >
        metadata filters 可以限制語言、出版社、
        主題及出版年份。

    - id: "IT-005"
      description: >
        include_details=false 時只回傳 ISBN 清單。

    - id: "IT-006"
      description: >
        include_details=true 時回傳 ISBN、
        書名與相關評分。

acceptance_criteria:
  - id: "AC-001"
    description: >
      Client 可以透過 POST /api/v1/books/search
      傳入自然語言查詢。

  - id: "AC-002"
    description: >
      系統使用與圖書匯入相同的 Embedding Model
      產生查詢向量。

  - id: "AC-003"
    description: >
      系統可以使用查詢向量搜尋
      Qdrant books collection。

  - id: "AC-004"
    description: >
      Qdrant 搜尋結果包含完整 payload。

  - id: "AC-005"
    description: >
      系統可以將 Qdrant 候選圖書交由 LLM
      過濾及重新排序。

  - id: "AC-006"
    description: >
      LLM 只能選擇候選清單中存在的 candidate_id。

  - id: "AC-007"
    description: >
      最終 ISBN 只能由後端從 Qdrant payload 取出，
      不可直接採用 LLM 產生值。

  - id: "AC-008"
    description: >
      API 以 JSON 格式回傳符合條件的 ISBN 陣列。

  - id: "AC-009"
    description: >
      找不到符合圖書時回傳 HTTP 200 及空 ISBN 陣列。

  - id: "AC-010"
    description: >
      LLM 無法使用時，系統可以降級使用
      Qdrant 向量相似度結果。

  - id: "AC-011"
    description: >
      API 可以選擇只回傳 ISBN，
      或附帶圖書詳細資料及評分。

  - id: "AC-012"
    description: >
      系統提供 API Key 驗證、輸入限制及統一錯誤格式。

future_extensions:
  phase_3:
    - "支援 Hybrid Search：向量搜尋加關鍵字全文搜尋"
    - "使用專用 Cross-Encoder Reranker 降低 LLM 成本"
    - "支援多 Collection 或多館圖書資料"
    - "支援查詢條件自動解析為 Qdrant metadata filters"
    - "加入 Redis 查詢快取"
    - "加入查詢歷史與使用統計"
    - "將結果回傳至既有圖書館系統"
    - "支援分頁與游標查詢"
    - "支援依館藏狀態與分館過濾"
```
