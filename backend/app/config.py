import os


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "books_collection")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_EMBED_DIMENSIONS = int(os.getenv("OLLAMA_EMBED_DIMENSIONS", "768"))
IMPORT_BATCH_SIZE = int(os.getenv("IMPORT_BATCH_SIZE", "100"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
MAX_RECORDS = int(os.getenv("MAX_RECORDS", "100000"))
MAX_JSON_DEPTH = int(os.getenv("MAX_JSON_DEPTH", "20"))
SCHEMA_VERSION = "MVP-v1"
