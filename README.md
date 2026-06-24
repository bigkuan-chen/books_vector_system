# Book Vector Database Importer

MVP-v1 implements a web importer for book JSON files. It validates records, embeds importable books with local Ollama embeddings, and writes points to the local Qdrant collection `books_collection`.

## Run Qdrant

```powershell
docker compose up -d
```

## Run Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Qdrant

Default connection:

```text
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=books_collection
EMBEDDING_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_EMBED_DIMENSIONS=768
```

Dashboard:

```text
http://localhost:6333/dashboard#/collections/books_collection
```

## Payload Contract

Each Qdrant point uses deterministic UUIDv5 from normalized ISBN:

```text
uuid5(URL_NAMESPACE, "book:{normalized_isbn}")
```

The complete original JSON object is stored in:

```text
payload.source_data
```
