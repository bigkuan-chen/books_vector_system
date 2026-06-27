# 圖書向量資料庫查詢與匯入系統 (Book Vector Database System)

提供一個網頁操作介面與 FastAPI 後端，能將圖書 JSON 資料匯入 Qdrant 向量資料庫中，並提供自然語言查詢介面，結合向量檢索與 LLM 重新排序（Reranking）來精準篩選出圖書資訊。

**Live Demo**: [Book Vector System](https://books-vector-system.vercel.app/book-search)

---

## 系統功能

1. **圖書向量資料庫匯入**：
   * 支援上傳包含書籍資料的 JSON 檔案。
   * 提供前置資料驗證（欄位完整性、格式校驗、ISBN 重複性檢查等）與視覺化預覽。
   * 設定重複處理原則（更新/忽略/拒絕）並支援大檔案的批次匯入處理。
2. **自然語言語意檢索**：
   * 使用者可以輸入自然語言描述需求，系統會進行向量特徵比對進行模糊語意查詢。
3. **中介資料篩選 (Metadata Filtering)**：
   * 支援針對語言（zh-TW, zh-CN, en, ja）、出版社、主題標籤、出版年份範圍等進行混合精確篩選。
4. **LLM 重新排序與過濾 (Reranking)**：
   * 粗篩出的候選書籍會再送至 LLM，對照使用者查詢進行二次精確相關度評分。
   * 排除未達 `llm_min_score` 的書籍，並調整最终排序。
5. **詳細查詢統計與偵錯**：
   * 圖表展示查詢耗時分析（向量檢索耗時、LLM 耗時比例）。
   * 完整呈現 LLM 系統提示詞、模型輸入內容、模型原始 JSON 與解析結果，便於偵錯。

---

## 技術選型 (Tech Stack)

* **後端 (Backend)**:
  * **核心框架**: Python 3.10+, FastAPI (高性能非同步 API 框架)
  * **Web 伺服器**: Uvicorn
  * **向量資料庫**: Qdrant (高效能向量搜尋引擎)
  * **向量 Embedding**: Ollama / Sentence-Transformers
  * **大語言模型**: OpenAI 相容 API 介面 (如本地 Ollama 或是外部雲端 LLM API)
* **前端 (Frontend)**:
  * **核心框架**: Next.js 16 (App Router)、React 19 (TypeScript)
  * **樣式設計**: Tailwind CSS、Lucide Icons

---

## 系統查詢架構 (Search Architecture)

系統採用兩階段檢索（Retrieve & Rerank）的混合式搜尋架構：

```
                    ┌────────────────────────┐
                    │  使用者輸入自然語言查詢  │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │   文本向量化 (Embed)   │
                    └───────────┬────────────┘
                                │ (查詢向量)
                                ▼
                    ┌────────────────────────┐
                    │   Qdrant 向量檢索      ├──────────◄ [中介資料篩選 (Filters)]
                    └───────────┬────────────┘
                                │
                                ▼ (得到 N 筆 Candidate)
                    ┌───────────┴────────────┐
                    │      向量分數篩選      │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌───────────┴────────────┐
                    │     LLM 重新排序       ├──────────◄ [自訂系統提示詞]
                    │      (Reranking)       │
                    └───────────┬────────────┘
                                │ (LLM 分數篩選 / 重新排序)
                                ▼
                    ┌───────────┴────────────┐
                    │   最終回傳及統計顯示   │
                    └────────────────────────┘
```

1. **第一階段 - 粗篩 (Vector Search)**:
   * 將查詢文本轉換為特徵向量，在 Qdrant 資料庫中進行 Cosine Similarity 計算。
   * 套用中介資料篩選（如年份、出版社）與向量分數門檻（Score Threshold）。
   * 撈出最多 `candidate_limit` 筆候選資料。
2. **第二階段 - 精篩 (LLM Rerank)**:
   * 將第一階段得到的候選書籍清單、自訂系統提示詞、使用者查詢組裝後，發送給語言模型。
   * LLM 獨立評估每本候選書，回傳 0.0 ~ 1.0 的相關度分數與理由。
   * 排除分數低於 `llm_min_score` 的書籍，並按 LLM 分數由高到低排序，最終截取前 `top_k` 筆最相關的圖書回傳給前端。

---

## 系統操作流程

### 1. 資料庫建檔 (Import Flow)
1. 進入系統首頁（圖書向量資料庫匯入）。
2. 點擊「瀏覽」選擇 JSON 書籍檔案，查看下方即時資料預覽。
3. 點擊 **「檢查資料」**，系統將以條列與指標卡呈現資料驗證結果。
4. 設定匯入選項，點擊 **「匯入向量資料庫」**。
5. 匯入進度條會即時更新目前已處理的資料筆數與狀態。

### 2. 語意查詢與分析 (Search Flow)
1. 點擊頂部導覽列前往 **「圖書向量資料查詢」** 頁面。
2. 於「查詢文字」輸入需求，或選取預設的「查詢範例」。
3. 在左側 **「參數」** 側邊欄調整過濾和搜尋參數。
4. 點擊 **「查詢」**。
5. 查詢完成後，右側將顯示：
   * 查詢耗時比例條與統計資訊。
   * 書籍卡片清單（顯示書籍資訊、向量分數、LLM 分數與 LLM 評估原因）。
   * 後端 Debug 面板（系統提示詞、輸入候選、原始 LLM Response 等）。

---

## 向量查詢與過濾參數設定說明

您可在側邊欄的 **「參數」** 面板自訂以下數值，這些設定會直接影響搜尋效率與推薦品質：

| 參數名稱 | API 欄位名稱 | 預設值 (可於環境設定變更) | 允許範圍 | 功能與運作行為說明 |
| :--- | :--- | :--- | :--- | :--- |
| **分數門檻** | `score_threshold` | `0.5` | `0.0 ~ 1.0` | **Qdrant 向量相似度最低門檻**。只有相似度分數高於此值的圖書才會被納入候選。若設為空值（不限制）則不會在粗篩階段進行分數過濾。 |
| **候選數量** | `candidate_limit` | `10` | `5 ~ 100` | **Qdrant 第一階段粗篩筆數**。這代表要交給 LLM 重排評估的圖書數量。**數值越大，檢索完整度越高，但會顯著增加 LLM 的處理時間與 Token 花費。** |
| **LLM 最低分** | `llm_min_score` | `0.60` | `0.0 ~ 1.0` | **LLM 二次篩選過濾閾值**。只有當大模型評估該書的語意分數大於等於此閾值時，才會呈現給使用者。 |
| **Top K** | `top_k` | `10` | `1 ~ 50` | **最終回傳與呈現的圖書筆數上限**。經過過濾與 Reranking 重排後，回傳評分最高的前 K 筆結果。 |
| **API 逾時 (秒)** | `api_timeout_seconds` | `90` | `1 ~ 600` | **API 請求逾時限制**。若 LLM 評估或 API 響應時間超過此秒數，後端將會中止該請求，並自動降級為僅依據 Qdrant 原始向量相似度排序回傳，以防網頁卡死。 |

---

## 啟動與執行說明

### 1. Docker 容器啟動 (推薦)
使用 Docker Compose 啟動包含 Qdrant 與 API 的完整環境：
```powershell
docker compose up --build
```
服務網址：
* Qdrant 控制台: `http://localhost:6333`
* API 文件 (Swagger): `http://localhost:8001/docs`

---

### 2. 本地手動啟動

#### 後端啟動 (FastAPI)
1. 進入 `backend` 目錄：
   ```powershell
   cd backend
   ```
2. 建立並啟用 Python 虛擬環境：
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. 安裝依賴套件：
   ```powershell
   pip install -r requirements.txt
   ```
4. 啟動 Uvicorn 伺服器：
   ```powershell
   uvicorn app.main:app --reload --port 8001
   ```

#### 前端啟動 (Next.js)
1. 進入 `frontend` 目錄：
   ```powershell
   cd frontend
   ```
2. 安裝套件依賴：
   ```powershell
   npm install
   ```
3. 啟動前端開發伺服器：
   ```powershell
   npm run dev -- -p 3001
   ```
4. 瀏覽網頁：開啟瀏覽器前往 `http://localhost:3001/book-search`。

---

## 環境變數設定 (.env)

複製根目錄的 `.env.example` 為 `.env` 或修改 `frontend/.env.local` 檔案來進行設定：

* `QDRANT_URL`: Qdrant 服務端點 URL。
* `QDRANT_API_KEY`: Qdrant API 金鑰 (選填)。
* `EMBEDDING_PROVIDER`: `ollama` 或 `openai` 或是其他向量服務供應商。
* `LLM_PROVIDER`: `openai-compatible`。
* `LLM_API_BASE`: OpenAI 相容 API 端點 URL。
* `LLM_MODEL`: 使用的 LLM 模型名稱。
* `API_TIMEOUT_SECONDS`: 預設的 API 逾時秒數。
* `NEXT_PUBLIC_DEFAULT_TOP_K`: 前端 UI 預設 Top K。
* `NEXT_PUBLIC_DEFAULT_CANDIDATE_LIMIT`: 前端 UI 預設候選數量。
* `NEXT_PUBLIC_DEFAULT_SCORE_THRESHOLD`: 前端 UI 預設分數門檻。
* `NEXT_PUBLIC_DEFAULT_LLM_MIN_SCORE`: 前端 UI 預設 LLM 最低分。

---

## 資料結構契約與 deterministic UUID

* **結果擷取方式**：
  查詢結果自 Qdrant 點 Payload 中擷取以下欄位的 ISBN：
  * `payload.isbn`
  * `payload.source_data.isbn`
* **deterministic UUID 產生原則**：
  匯入時，系統會針對標準化後的 ISBN 生成 deterministic UUIDv5 作為 Qdrant 的 point 唯一識別碼：
  ```python
  uuid5(URL_NAMESPACE, "book:{normalized_isbn}")
  ```
