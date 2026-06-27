import os

def load_env_file():
    current = os.path.abspath(os.getcwd())
    for _ in range(3):
        path = os.path.join(current, ".env")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key, val = parts[0].strip(), parts[1].strip()
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        if key not in os.environ:
                            os.environ[key] = val
            break
        current = os.path.dirname(current)

load_env_file()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
print(f"[DEBUG] Loaded QDRANT_URL: {QDRANT_URL}", flush=True)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "books_collection")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
EMBEDDING_NORMALIZE = os.getenv("EMBEDDING_NORMALIZE", "true").lower() == "true"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_EMBED_DIMENSIONS = int(os.getenv("OLLAMA_EMBED_DIMENSIONS", "768"))
IMPORT_BATCH_SIZE = int(os.getenv("IMPORT_BATCH_SIZE", "100"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
MAX_RECORDS = int(os.getenv("MAX_RECORDS", "100000"))
MAX_JSON_DEPTH = int(os.getenv("MAX_JSON_DEPTH", "20"))
BOOK_QUERY_API_KEY = os.getenv("BOOK_QUERY_API_KEY", "change-me")
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "10"))
DEFAULT_CANDIDATE_LIMIT = int(os.getenv("DEFAULT_CANDIDATE_LIMIT", "30"))
DEFAULT_SCORE_THRESHOLD = os.getenv("DEFAULT_SCORE_THRESHOLD", "")
DEFAULT_LLM_MIN_SCORE = float(os.getenv("DEFAULT_LLM_MIN_SCORE", "0.60"))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai-compatible")
LLM_API_BASE = os.getenv("LLM_API_BASE", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "45"))
LOG_QUERY_CONTENT = os.getenv("LOG_QUERY_CONTENT", "false").lower() == "true"
SCHEMA_VERSION = "MVP-v3"
