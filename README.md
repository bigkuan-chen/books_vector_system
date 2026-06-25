# Book Vector Database Query System

MVP-v2 provides a FastAPI service for importing book JSON into Qdrant and searching the `books` collection with natural-language queries.

The search path embeds the query, retrieves Qdrant candidates, optionally asks an OpenAI-compatible LLM to rerank candidate IDs, and always returns ISBNs from Qdrant payload data.

## Run With Docker

```powershell
docker compose up --build
```

Services:

```text
Qdrant: http://localhost:6333
API:     http://localhost:8001
```

## Run Backend Locally

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3001`.

Search UI:

```text
http://127.0.0.1:3001/book-search
```

## Search API

```http
POST /api/books/search
Content-Type: application/json
X-API-Key: <BOOK_QUERY_API_KEY, only required when set to a value other than change-me>
```

Example:

```json
{
  "query": "適合初學者學 Python 資料分析，包含 pandas 與實作練習",
  "top_k": 5,
  "candidate_limit": 30,
  "score_threshold": 0.35,
  "llm_min_score": 0.65,
  "use_llm_rerank": true,
  "include_details": true,
  "filters": {
    "language": "zh-TW",
    "subjects": ["Python", "資料分析"],
    "publish_year_from": 2020
  }
}
```

Health:

```http
GET /api/health
GET /api/health/qdrant
```

## Environment

Copy `.env.example` to `.env` for local overrides. Important defaults:

```text
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=books
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=intfloat/multilingual-e5-small
BOOK_QUERY_API_KEY=change-me
```

LLM reranking is optional. Configure these to enable it:

```text
LLM_API_BASE=https://your-openai-compatible-endpoint/v1
LLM_API_KEY=...
LLM_MODEL=...
```

When LLM reranking is unavailable or invalid, the API falls back to Qdrant vector-score ranking.

## Payload Contract

Search results extract ISBN only from Qdrant payload:

```text
payload.isbn
payload.source_data.isbn
```

The importer writes the original JSON object as the point payload and uses deterministic UUIDv5 point IDs from normalized ISBN:

```text
uuid5(URL_NAMESPACE, "book:{normalized_isbn}")
```
