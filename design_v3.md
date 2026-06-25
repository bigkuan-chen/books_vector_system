```yaml
project:
  name: "Book Vector Database System"
  display_name: "圖書向量資料庫系統"
  version: "MVP-v3"
  language: "zh-TW"

feature:
  id: "BOOK-VECTOR-SEARCH"
  name: "圖書向量資料查詢"
  route: "/book-search"

  description: >
    提供網頁操作介面，讓使用者輸入自然語言查詢文字，
    設定向量查詢、LLM 過濾及結果回傳參數。
    使用者按下查詢按鈕後，前端透過 RESTful API 呼叫
    http://localhost:8000/api/books/search。
    系統取得 API 回傳結果後，將 Response 中的所有欄位
    完整顯示於查詢結果區域。

  goals:
    - "輸入自然語言圖書查詢條件"
    - "設定向量查詢參數"
    - "設定 LLM 過濾參數"
    - "呼叫圖書查詢 RESTful API"
    - "顯示 API 回傳的所有欄位"
    - "顯示 ISBN 查詢結果"
    - "顯示圖書詳細資料"
    - "顯示向量分數、LLM 分數及最終分數"
    - "顯示查詢執行統計資訊"
    - "顯示 API 錯誤訊息"
    - "提供原始 JSON Response 檢視"

navigation:
  menu:
    - id: "NAV-IMPORT"
      label: "圖書資料匯入"
      route: "/book-import"
      icon: "upload"

    - id: "NAV-SEARCH"
      label: "圖書向量資料查詢"
      route: "/book-search"
      icon: "search"
      active: true

page:
  id: "PAGE-BOOK-SEARCH"
  title: "圖書向量資料查詢"

  subtitle: >
    使用自然語言描述想查詢的圖書，
    系統將透過向量搜尋及 LLM 過濾取得相關圖書。

  layout:
    type: "responsive"
    desktop:
      columns: 2
      left_width: "40%"
      right_width: "60%"

    tablet:
      columns: 1

    mobile:
      columns: 1

  sections:
    - id: "SEARCH-CONDITION"
      title: "查詢條件"
      position: "left"
      order: 1

    - id: "SEARCH-PARAMETERS"
      title: "查詢參數設定"
      position: "left"
      order: 2
      collapsible: true
      default_expanded: true

    - id: "API-STATUS"
      title: "API 連線狀態"
      position: "left"
      order: 3

    - id: "SEARCH-SUMMARY"
      title: "查詢摘要"
      position: "right"
      order: 1

    - id: "SEARCH-RESULTS"
      title: "查詢結果"
      position: "right"
      order: 2

    - id: "RAW-JSON"
      title: "原始 JSON Response"
      position: "right"
      order: 3
      collapsible: true
      default_expanded: false

search_form:
  id: "BOOK-SEARCH-FORM"

  fields:
    query:
      component: "textarea"
      label: "查詢文字"
      name: "query"

      placeholder: >
        例如：找適合 Python 初學者閱讀的資料分析書籍，
        希望內容包含 pandas、資料視覺化及實作案例。

      required: true
      min_length: 1
      max_length: 2000
      rows: 6

      help_text: >
        請使用自然語言描述想查詢的圖書主題、
        適用程度、語言、內容或出版條件。

      validation:
        trim: true
        reject_blank: true

        messages:
          required: "請輸入想查詢的文字"
          max_length: "查詢文字不可超過 2000 個字元"

      counter:
        enabled: true
        format: "{current}/2000"

    example_queries:
      component: "select"
      label: "查詢範例"
      name: "example_query"

      placeholder: "選擇查詢範例"

      options:
        - label: "Python 資料分析入門"
          value: >
            找適合 Python 初學者的資料分析書籍，
            希望包含 pandas、NumPy、資料視覺化及實作案例。

        - label: "人工智慧基礎"
          value: >
            查詢介紹人工智慧、機器學習與深度學習基礎概念的中文書籍，
            適合沒有相關經驗的初學者閱讀。

        - label: "FastAPI 網頁開發"
          value: >
            找使用 Python FastAPI 開發 RESTful API 的實作書籍，
            希望包含資料庫、驗證、部署及測試內容。

        - label: "投資理財"
          value: >
            查詢適合一般讀者閱讀的股票投資與財務分析書籍，
            希望包含基本面分析與風險管理。

      behavior:
        on_change: "copy_value_to_query"

parameter_settings:
  display:
    component: "accordion"
    label: "進階查詢參數"
    default_expanded: true

  groups:
    - id: "VECTOR-SETTINGS"
      title: "向量搜尋設定"

      fields:
        top_k:
          component: "number"
          label: "最終回傳筆數"
          name: "top_k"
          default: 10
          minimum: 1
          maximum: 50
          step: 1

          help_text: >
            經過向量搜尋與 LLM 過濾後，
            最多回傳的圖書數量。

        candidate_limit:
          component: "number"
          label: "Qdrant 候選筆數"
          name: "candidate_limit"
          default: 30
          minimum: 5
          maximum: 100
          step: 1

          help_text: >
            從 Qdrant 取得並交給 LLM 比較的候選圖書數量。

          validation:
            rules:
              - expression: "candidate_limit >= top_k"
                message: "Qdrant 候選筆數不可小於最終回傳筆數"

        score_threshold:
          component: "number"
          label: "向量最低相似度"
          name: "score_threshold"
          default: null
          minimum: 0
          maximum: 1
          step: 0.01

          placeholder: "不設定"

          allow_null: true

          help_text: >
            只取得向量相似度高於此數值的候選圖書。
            留空表示不設定最低門檻。

    - id: "LLM-SETTINGS"
      title: "LLM 過濾設定"

      fields:
        use_llm_rerank:
          component: "switch"
          label: "啟用 LLM 過濾與重新排序"
          name: "use_llm_rerank"
          default: true

          help_text: >
            使用 LLM 比較自然語言查詢條件與候選圖書，
            排除不符合的資料並重新排序。

        llm_min_score:
          component: "number"
          label: "LLM 最低符合分數"
          name: "llm_min_score"
          default: 0.6
          minimum: 0
          maximum: 1
          step: 0.05

          enabled_when:
            field: "use_llm_rerank"
            equals: true

          help_text: >
            LLM 判斷符合程度低於此分數的圖書將被排除。

    - id: "RESPONSE-SETTINGS"
      title: "回傳資料設定"

      fields:
        include_details:
          component: "switch"
          label: "回傳圖書詳細資料"
          name: "include_details"
          default: true

          help_text: >
            啟用後，API 除 ISBN 外也會回傳書名、
            向量分數、LLM 分數、最終分數及符合原因。

    - id: "FILTER-SETTINGS"
      title: "Payload 條件過濾"

      fields:
        language:
          component: "select"
          label: "語言"
          name: "filters.language"
          default: null
          clearable: true

          options:
            - label: "全部語言"
              value: null

            - label: "繁體中文"
              value: "zh-TW"

            - label: "簡體中文"
              value: "zh-CN"

            - label: "英文"
              value: "en"

            - label: "日文"
              value: "ja"

        publisher:
          component: "text"
          label: "出版社"
          name: "filters.publisher"
          default: null
          max_length: 200
          placeholder: "例如：碁峰資訊"

        subjects:
          component: "tag_input"
          label: "主題分類"
          name: "filters.subjects"
          default: []

          placeholder: "輸入主題後按 Enter"

          examples:
            - "Python"
            - "資料分析"
            - "人工智慧"
            - "機器學習"

        publish_year_from:
          component: "number"
          label: "出版年份起"
          name: "filters.publish_year_from"
          default: null
          minimum: 1000
          maximum: 2100
          step: 1
          placeholder: "例如：2020"

        publish_year_to:
          component: "number"
          label: "出版年份迄"
          name: "filters.publish_year_to"
          default: null
          minimum: 1000
          maximum: 2100
          step: 1
          placeholder: "例如：2026"

          validation:
            rules:
              - expression: >
                  publish_year_to == null ||
                  publish_year_from == null ||
                  publish_year_to >= publish_year_from

                message: "出版年份迄不可小於出版年份起"

form_actions:
  buttons:
    search:
      id: "BTN-SEARCH"
      component: "button"
      type: "submit"
      label: "查詢"
      icon: "search"
      style: "primary"

      enabled_when:
        - "query_is_not_blank"
        - "form_is_valid"
        - "request_is_not_loading"

      loading:
        label: "查詢中..."
        show_spinner: true

    clear:
      id: "BTN-CLEAR"
      component: "button"
      type: "button"
      label: "清除"
      icon: "clear"
      style: "secondary"

      action:
        - "reset_form"
        - "clear_search_results"
        - "clear_error_message"
        - "clear_raw_json"

    reset_parameters:
      id: "BTN-RESET-PARAMETERS"
      component: "button"
      type: "button"
      label: "恢復預設參數"
      icon: "settings_backup_restore"
      style: "text"

      action:
        - "reset_parameter_fields_only"

api:
  id: "BOOK-SEARCH-API"

  method: "POST"
  url: "http://localhost:8000/api/books/search"
  content_type: "application/json"
  accept: "application/json"

  timeout_ms: 45000

  headers:
    Content-Type: "application/json"
    Accept: "application/json"

  optional_headers:
    X-API-Key:
      enabled: false
      value_source: "environment.NEXT_PUBLIC_BOOK_QUERY_API_KEY"

  request_mapping:
    query:
      source: "form.query"
      type: "string"
      required: true

    top_k:
      source: "form.top_k"
      type: "integer"
      default: 10

    candidate_limit:
      source: "form.candidate_limit"
      type: "integer"
      default: 30

    score_threshold:
      source: "form.score_threshold"
      type:
        - "number"
        - "null"
      default: null

    llm_min_score:
      source: "form.llm_min_score"
      type: "number"
      default: 0.6

    use_llm_rerank:
      source: "form.use_llm_rerank"
      type: "boolean"
      default: true

    include_details:
      source: "form.include_details"
      type: "boolean"
      default: true

    filters:
      source: "form.filters"
      type: "object"

      properties:
        language:
          source: "form.filters.language"
          omit_when_null: true

        publisher:
          source: "form.filters.publisher"
          omit_when_blank: true

        subjects:
          source: "form.filters.subjects"
          omit_when_empty: true

        publish_year_from:
          source: "form.filters.publish_year_from"
          omit_when_null: true

        publish_year_to:
          source: "form.filters.publish_year_to"
          omit_when_null: true

      omit_when_empty: true

  request_example:
    query: >
      找適合 Python 初學者的資料分析書籍，
      希望包含 pandas、資料視覺化及實作案例。

    top_k: 10
    candidate_limit: 30
    score_threshold: 0.35
    llm_min_score: 0.6
    use_llm_rerank: true
    include_details: true

    filters:
      language: "zh-TW"
      publisher: null

      subjects:
        - "Python"
        - "資料分析"

      publish_year_from: 2020
      publish_year_to: 2026

  request_processing:
    before_send:
      - "trim_query"
      - "validate_required_fields"
      - "validate_parameter_range"
      - "remove_null_filter_fields"
      - "remove_empty_filter_fields"
      - "set_loading_true"
      - "clear_previous_error"

    after_success:
      - "store_response"
      - "display_all_response_fields"
      - "set_loading_false"
      - "scroll_to_result"

    after_error:
      - "store_error_response"
      - "display_error_message"
      - "set_loading_false"

api_status:
  states:
    idle:
      label: "尚未查詢"
      icon: "circle"
      severity: "neutral"

    loading:
      label: "正在呼叫查詢 API"
      icon: "spinner"
      severity: "info"

    success:
      label: "查詢成功"
      icon: "check_circle"
      severity: "success"

    empty:
      label: "查詢成功，但沒有符合的圖書"
      icon: "info"
      severity: "warning"

    error:
      label: "查詢失敗"
      icon: "error"
      severity: "error"

search_response:
  expected_schema:
    type: "object"

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

        items:
          type: "object"

          known_properties:
            isbn:
              type: "string"

            title:
              type: "string"

            authors:
              type:
                - "array"
                - "string"
                - "null"

            publisher:
              type:
                - "string"
                - "null"

            publish_date:
              type:
                - "string"
                - "number"
                - "null"

            language:
              type:
                - "string"
                - "null"

            subjects:
              type:
                - "array"
                - "string"
                - "null"

            description:
              type:
                - "string"
                - "null"

            vector_score:
              type:
                - "number"
                - "null"

            llm_score:
              type:
                - "number"
                - "null"

            final_score:
              type:
                - "number"
                - "null"

            reason:
              type:
                - "string"
                - "null"

            payload:
              type:
                - "object"
                - "null"

          additional_properties:
            allowed: true
            display: true

      metadata:
        type: "object"

        known_properties:
          qdrant_candidates:
            type: "integer"

          llm_filtered_candidates:
            type: "integer"

          returned_results:
            type: "integer"

          llm_rerank_used:
            type: "boolean"

          fallback_reason:
            type:
              - "string"
              - "null"

          elapsed_ms:
            type: "integer"

        additional_properties:
          allowed: true
          display: true

      error:
        type:
          - "object"
          - "null"

        properties:
          code:
            type: "string"

          message:
            type: "string"

          details:
            type:
              - "object"
              - "string"
              - "array"
              - "null"

    additional_properties:
      allowed: true
      display: true

result_display:
  rule: >
    API Response 中所有已知欄位與未知欄位都必須顯示。
    不可因為前端沒有預先定義欄位而忽略資料。

  summary_cards:
    enabled: true

    fields:
      request_id:
        label: "Request ID"
        source: "response.request_id"
        display_when_exists: true

      count:
        label: "回傳圖書數量"
        source: "response.count"
        default: 0

      qdrant_candidates:
        label: "Qdrant 候選數量"
        source: "response.metadata.qdrant_candidates"
        display_when_exists: true

      llm_filtered_candidates:
        label: "LLM 過濾後數量"
        source: "response.metadata.llm_filtered_candidates"
        display_when_exists: true

      elapsed_ms:
        label: "查詢時間"
        source: "response.metadata.elapsed_ms"
        suffix: " ms"
        display_when_exists: true

      llm_rerank_used:
        label: "使用 LLM 排序"
        source: "response.metadata.llm_rerank_used"

        format:
          true: "是"
          false: "否"

  query_display:
    enabled: true
    label: "實際查詢文字"
    source: "response.query"
    preserve_line_breaks: true

  isbn_list:
    enabled: true
    title: "符合的 ISBN"

    source: "response.isbns"

    empty_message: "沒有符合條件的 ISBN"

    item:
      show_index: true
      copy_button: true

    actions:
      copy_all:
        enabled: true
        label: "複製全部 ISBN"

      download_json:
        enabled: true
        label: "下載 ISBN JSON"
        filename: "book-search-isbns.json"

  results_table:
    enabled: true
    title: "圖書詳細結果"

    source: "response.results"

    empty_message: "沒有圖書詳細結果"

    behavior:
      responsive: true
      horizontal_scroll: true
      sortable: true
      filterable: true
      pagination: true
      default_page_size: 10

      page_size_options:
        - 10
        - 20
        - 50
        - 100

      row_expandable: true

    columns:
      - key: "rank"
        label: "排名"
        generated: true
        source: "row_index + 1"
        sortable: true

      - key: "isbn"
        label: "ISBN"
        source: "result.isbn"
        sortable: true
        searchable: true
        copy_button: true

      - key: "title"
        label: "書名"
        source: "result.title"
        sortable: true
        searchable: true

      - key: "authors"
        label: "作者"
        source: "result.authors"

        formatter:
          array: "join_with_comma"
          null: "-"

      - key: "publisher"
        label: "出版社"
        source: "result.publisher"
        sortable: true
        searchable: true

      - key: "publish_date"
        label: "出版日期"
        source: "result.publish_date"
        sortable: true

      - key: "language"
        label: "語言"
        source: "result.language"
        sortable: true

      - key: "subjects"
        label: "主題"
        source: "result.subjects"

        formatter:
          array: "display_as_tags"
          string: "display_as_tag"
          null: "-"

      - key: "vector_score"
        label: "向量分數"
        source: "result.vector_score"
        sortable: true

        formatter:
          type: "decimal"
          decimal_places: 4

      - key: "llm_score"
        label: "LLM 分數"
        source: "result.llm_score"
        sortable: true

        formatter:
          type: "decimal"
          decimal_places: 4

      - key: "final_score"
        label: "最終分數"
        source: "result.final_score"
        sortable: true

        formatter:
          type: "decimal"
          decimal_places: 4

      - key: "reason"
        label: "符合原因"
        source: "result.reason"
        wrap_text: true

      - key: "actions"
        label: "操作"
        generated: true

        buttons:
          - id: "VIEW-DETAIL"
            label: "查看完整資料"
            icon: "visibility"
            action: "open_result_detail_dialog"

          - id: "COPY-RESULT"
            label: "複製 JSON"
            icon: "content_copy"
            action: "copy_current_result_json"

    dynamic_columns:
      enabled: true

      rule: >
        如果 API results 內包含 columns 未定義的其他欄位，
        前端應自動建立額外欄位或在展開區顯示，
        不可忽略任何回傳欄位。

  result_detail_dialog:
    enabled: true
    title_template: "圖書完整資料：{title}"

    sections:
      basic_information:
        title: "基本資料"

        fields:
          - "isbn"
          - "title"
          - "authors"
          - "publisher"
          - "publish_date"
          - "language"
          - "subjects"
          - "description"

      score_information:
        title: "查詢評分"

        fields:
          - "vector_score"
          - "llm_score"
          - "final_score"
          - "reason"

      payload_information:
        title: "Payload 完整資料"
        source: "result.payload"

        display:
          type: "json_tree"
          expandable: true
          copy_button: true

      additional_information:
        title: "其他回傳欄位"

        source: "result.additional_properties"

        display:
          type: "key_value_table"
          show_all: true

  metadata_display:
    enabled: true
    title: "查詢執行資訊"

    source: "response.metadata"

    display:
      type: "key_value_table"
      show_all: true

    known_fields:
      qdrant_candidates:
        label: "Qdrant 候選圖書數"

      llm_filtered_candidates:
        label: "LLM 過濾後圖書數"

      returned_results:
        label: "實際回傳圖書數"

      llm_rerank_used:
        label: "是否使用 LLM 重新排序"

      fallback_reason:
        label: "降級處理原因"

      elapsed_ms:
        label: "總執行時間"

    unknown_fields:
      display: true
      label_strategy: "use_original_key"

raw_json_viewer:
  enabled: true
  title: "原始 JSON Response"

  source: "complete_api_response"

  component: "json_viewer"

  options:
    syntax_highlight: true
    expandable: true
    default_expand_depth: 3
    show_line_numbers: true
    wrap_long_lines: true
    copy_button: true
    download_button: true
    search: true

  download:
    filename_template: "book-search-{request_id}.json"
    content_type: "application/json"

empty_state:
  before_search:
    title: "尚未進行查詢"

    message: >
      請在左側輸入想查詢的圖書內容，
      設定查詢參數後按下「查詢」。

    icon: "manage_search"

  no_results:
    title: "找不到符合的圖書"

    message: >
      可以修改查詢文字、降低最低相似度、
      降低 LLM 最低分數或取消部分過濾條件後重新查詢。

    icon: "search_off"

loading_state:
  enabled: true

  overlay:
    show: false

  search_button:
    show_spinner: true
    label: "查詢中..."

  result_area:
    component: "skeleton"

    rows: 5

  message: >
    正在產生查詢向量、搜尋 Qdrant 並使用 LLM 過濾資料。

error_display:
  enabled: true
  component: "alert"

  show_fields:
    - "http_status"
    - "error.code"
    - "error.message"
    - "error.details"
    - "request_id"

  mappings:
    network_error:
      title: "無法連接查詢服務"

      message: >
        無法連接 http://localhost:8000，
        請確認 FastAPI 服務是否已啟動。

    timeout:
      title: "查詢逾時"

      message: >
        API 查詢時間超過限制，
        請稍後重新查詢或降低候選圖書數量。

    invalid_request:
      title: "查詢參數錯誤"

    server_error:
      title: "伺服器發生錯誤"

    qdrant_error:
      title: "Qdrant 查詢失敗"

    llm_error:
      title: "LLM 過濾失敗"

  actions:
    retry:
      enabled: true
      label: "重新查詢"
      action: "submit_previous_request"

    copy_error:
      enabled: true
      label: "複製錯誤資訊"

frontend_state:
  store:
    query_form:
      query: ""
      top_k: 10
      candidate_limit: 30
      score_threshold: null
      llm_min_score: 0.6
      use_llm_rerank: true
      include_details: true

      filters:
        language: null
        publisher: null
        subjects: []
        publish_year_from: null
        publish_year_to: null

    request:
      loading: false
      submitted: false
      last_request_payload: null

    response:
      data: null
      raw_json: null

    error:
      has_error: false
      http_status: null
      code: null
      message: null
      details: null

frontend_behavior:
  submit_search:
    trigger:
      - "click BTN-SEARCH"
      - "keyboard Ctrl+Enter"

    steps:
      - step: 1
        action: "validate_form"

      - step: 2
        action: "build_request_payload"

      - step: 3
        action: "remove_empty_filter_values"

      - step: 4
        action: "set_loading_state"

      - step: 5
        action: "POST http://localhost:8000/api/books/search"

      - step: 6
        condition: "HTTP status is 2xx"
        action: "store_complete_response"

      - step: 7
        condition: "HTTP status is 2xx"
        action: "render_all_response_fields"

      - step: 8
        condition: "HTTP status is not 2xx"
        action: "render_error_response"

      - step: 9
        action: "clear_loading_state"

  keyboard_shortcuts:
    - keys: "Ctrl+Enter"
      action: "submit_search"

    - keys: "Escape"
      action: "close_dialog"

cors:
  frontend_origin:
    development:
      - "http://localhost:3000"
      - "http://127.0.0.1:3000"

  backend_requirement:
    allow_origins:
      - "http://localhost:3000"
      - "http://127.0.0.1:3000"

    allow_methods:
      - "GET"
      - "POST"
      - "OPTIONS"

    allow_headers:
      - "Content-Type"
      - "Accept"
      - "X-API-Key"

environment:
  frontend:
    file: ".env.local"

    variables:
      NEXT_PUBLIC_BOOK_SEARCH_API_URL: >
        http://localhost:8000/api/books/search

      NEXT_PUBLIC_BOOK_QUERY_API_KEY: ""

      NEXT_PUBLIC_API_TIMEOUT_MS: "45000"

project_structure:
  frontend:
    - path: "src/app/book-search/page.tsx"
      purpose: "圖書向量資料查詢主頁面"

    - path: "src/components/book-search/SearchForm.tsx"
      purpose: "自然語言查詢輸入表單"

    - path: "src/components/book-search/SearchParameters.tsx"
      purpose: "查詢參數設定元件"

    - path: "src/components/book-search/SearchSummary.tsx"
      purpose: "顯示查詢摘要與統計資訊"

    - path: "src/components/book-search/IsbnList.tsx"
      purpose: "顯示 ISBN 清單"

    - path: "src/components/book-search/SearchResultTable.tsx"
      purpose: "顯示圖書查詢結果表格"

    - path: "src/components/book-search/ResultDetailDialog.tsx"
      purpose: "顯示單筆圖書完整資料"

    - path: "src/components/book-search/RawJsonViewer.tsx"
      purpose: "顯示完整原始 JSON Response"

    - path: "src/components/book-search/SearchError.tsx"
      purpose: "顯示 API 錯誤資訊"

    - path: "src/services/bookSearchApi.ts"
      purpose: "封裝圖書查詢 RESTful API"

    - path: "src/types/bookSearch.ts"
      purpose: "Request 與 Response TypeScript 型別"

    - path: "src/hooks/useBookSearch.ts"
      purpose: "管理查詢流程與狀態"

    - path: "src/utils/responseFieldMapper.ts"
      purpose: "動態解析並顯示所有 API Response 欄位"

    - path: ".env.local"
      purpose: "前端 API URL 與環境設定"

typescript_models:
  BookSearchRequest:
    fields:
      query: "string"
      top_k: "number"
      candidate_limit: "number"
      score_threshold: "number | null"
      llm_min_score: "number"
      use_llm_rerank: "boolean"
      include_details: "boolean"
      filters: "BookSearchFilters | undefined"

  BookSearchFilters:
    fields:
      language: "string | null"
      publisher: "string | null"
      subjects: "string[]"
      publish_year_from: "number | null"
      publish_year_to: "number | null"

  BookSearchResult:
    fields:
      isbn: "string"
      title: "string | null"
      authors: "string[] | string | null"
      publisher: "string | null"
      publish_date: "string | number | null"
      language: "string | null"
      subjects: "string[] | string | null"
      description: "string | null"
      vector_score: "number | null"
      llm_score: "number | null"
      final_score: "number | null"
      reason: "string | null"
      payload: "Record<string, unknown> | null"
      additional_fields: "Record<string, unknown>"

  BookSearchResponse:
    fields:
      success: "boolean"
      request_id: "string | null"
      query: "string | null"
      count: "number"
      isbns: "string[]"
      results: "BookSearchResult[]"
      metadata: "Record<string, unknown>"
      error: "BookSearchError | null"
      additional_fields: "Record<string, unknown>"

responsive_design:
  desktop:
    search_form_position: "left"
    result_position: "right"
    result_table_mode: "full"

  tablet:
    search_form_position: "top"
    result_position: "bottom"
    result_table_mode: "horizontal_scroll"

  mobile:
    search_form_position: "top"
    result_position: "bottom"
    result_table_mode: "card"

    parameter_settings:
      collapsible: true
      default_expanded: false

    results:
      display: "cards"

      card_fields:
        - "isbn"
        - "title"
        - "authors"
        - "final_score"
        - "reason"

accessibility:
  enabled: true

  requirements:
    - "所有表單欄位都有 label"
    - "查詢按鈕支援鍵盤操作"
    - "錯誤訊息使用 aria-live"
    - "Loading 狀態使用 aria-busy"
    - "表格欄位具備正確 header"
    - "Dialog 開啟後焦點移入內容"
    - "Dialog 關閉後焦點回到原按鈕"

testing:
  unit_tests:
    - id: "UT-UI-001"
      description: "查詢文字為空時不可送出"

    - id: "UT-UI-002"
      description: "查詢文字超過 2000 字時顯示錯誤"

    - id: "UT-UI-003"
      description: "candidate_limit 小於 top_k 時顯示錯誤"

    - id: "UT-UI-004"
      description: "出版年份迄小於出版年份起時顯示錯誤"

    - id: "UT-UI-005"
      description: "空白及 null filter 不會放入 Request"

    - id: "UT-UI-006"
      description: "查詢中按鈕不可重複點擊"

    - id: "UT-UI-007"
      description: "API Response 的所有 ISBN 可正確顯示"

    - id: "UT-UI-008"
      description: "results 中未知欄位仍可顯示"

    - id: "UT-UI-009"
      description: "metadata 中未知欄位仍可顯示"

    - id: "UT-UI-010"
      description: "原始 JSON Response 可正確顯示與複製"

  integration_tests:
    - id: "IT-UI-001"
      description: >
        輸入查詢文字並按下查詢後，
        前端呼叫 POST http://localhost:8000/api/books/search。

    - id: "IT-UI-002"
      description: >
        查詢參數可正確轉換為 API Request JSON。

    - id: "IT-UI-003"
      description: >
        API 回傳成功後可顯示查詢摘要、ISBN、
        圖書詳細資料、metadata 及原始 JSON。

    - id: "IT-UI-004"
      description: >
        API 回傳 count=0 時顯示無結果畫面。

    - id: "IT-UI-005"
      description: >
        API 無法連線時顯示 localhost:8000
        連線錯誤訊息。

    - id: "IT-UI-006"
      description: >
        API 回傳非預期的新欄位時，
        前端仍可在動態欄位或 JSON Viewer 中顯示。

acceptance_criteria:
  - id: "AC-UI-001"
    description: >
      系統選單提供「圖書向量資料查詢」功能。

  - id: "AC-UI-002"
    description: >
      使用者可以輸入自然語言查詢文字。

  - id: "AC-UI-003"
    description: >
      UI 提供 top_k、candidate_limit、
      score_threshold、llm_min_score、
      use_llm_rerank 與 include_details 設定。

  - id: "AC-UI-004"
    description: >
      UI 提供語言、出版社、主題及出版年份過濾設定。

  - id: "AC-UI-005"
    description: >
      按下查詢後呼叫
      http://localhost:8000/api/books/search。

  - id: "AC-UI-006"
    description: >
      RESTful API 使用 POST 及 application/json。

  - id: "AC-UI-007"
    description: >
      查詢期間顯示 Loading 狀態，
      且不可重複送出 Request。

  - id: "AC-UI-008"
    description: >
      查詢成功後顯示 Response 的 success、
      request_id、query、count 及 isbns。

  - id: "AC-UI-009"
    description: >
      查詢成功後顯示 results 中每一本圖書的所有欄位。

  - id: "AC-UI-010"
    description: >
      查詢成功後顯示 metadata 中的所有欄位。

  - id: "AC-UI-011"
    description: >
      API 回傳未知欄位時，前端不可忽略，
      必須透過動態欄位或 JSON Viewer 顯示。

  - id: "AC-UI-012"
    description: >
      UI 提供完整原始 JSON Response 檢視、
      複製及下載功能。

  - id: "AC-UI-013"
    description: >
      查詢不到資料時顯示空結果畫面，
      而不是顯示系統錯誤。

  - id: "AC-UI-014"
    description: >
      API 發生錯誤時顯示 HTTP Status、
      error code、message 及 details。

  - id: "AC-UI-015"
    description: >
      UI 支援桌面、平板及手機版面。
```
