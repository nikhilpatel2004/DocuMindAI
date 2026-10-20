"""Application configuration loaded from environment variables.

All secrets and runtime settings live in ``.env``. The module exposes a
single ``settings`` object used throughout the application.
"""
from __future__ import annotations

import os
from pathlib import Path


def _load_env_file() -> None:
    """Load the project ``.env`` file so local settings take effect.

    Existing environment variables always win over ``.env`` values.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:  # dotenv is optional — plain env vars still work
        return
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if env_path.is_file():
        load_dotenv(env_path)


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Runtime configuration. All values come from the environment."""

    def __init__(self) -> None:
        # --- Application ---
        self.app_name = _env("APP_NAME", "DocuMind AI") or "DocuMind AI"
        self.api_prefix = "/api/v1"
        self.debug = _env_bool("DEBUG", False)

        # --- Security ---
        self.jwt_secret = _env("JWT_SECRET", "change-me-in-production") or "change-me-in-production"
        self.jwt_expire_minutes = _env_int("JWT_EXPIRE_MINUTES", 60 * 24)
        self.jwt_algorithm = "HS256"

        # --- Persistence ---
        raw_db = _env("DATABASE_URL") or _env("SQLITE_PATH")
        if raw_db and (raw_db.startswith("postgresql://") or raw_db.startswith("postgres://")):
            self.database_url = raw_db
            self.database_path = None
            self.is_postgres = True
        elif raw_db:
            self.database_path = Path(raw_db)
            self.database_url = f"sqlite:///{self.database_path}"
            self.is_postgres = False
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.database_path = Path(__file__).resolve().parents[2] / "data" / "documind.db"
            self.database_url = f"sqlite:///{self.database_path}"
            self.is_postgres = False
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # --- Uploads ---
        upload_dir = _env("UPLOAD_DIR")
        if upload_dir:
            self.upload_dir = Path(upload_dir)
        else:
            self.upload_dir = Path(__file__).resolve().parents[2] / "data" / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_upload_mb = _env_int("MAX_UPLOAD_MB", 20)
        self.max_upload_bytes = self.max_upload_mb * 1024 * 1024

        # --- Vector store (Qdrant) ---
        self.qdrant_url = _env("QDRANT_URL", "http://localhost:6333") or "http://localhost:6333"
        self.qdrant_collection = _env("QDRANT_COLLECTION", "documind_chunks") or "documind_chunks"
        self.qdrant_api_key = _env("QDRANT_API_KEY")
        # When set, Qdrant runs embedded inside the process with on-disk storage
        # at this path, so no Qdrant server is required.
        self.qdrant_local_path = _env("QDRANT_LOCAL_PATH")

        # --- LLM inference (KIE API) ---
        self.kie_api_key = _env("KIE_API_KEY", "") or ""
        self.openai_base_url = _env("OPENAI_BASE_URL", "https://api.kie.ai/codex/v1") or "https://api.kie.ai/codex/v1"
        self.openai_model = _env("OPENAI_MODEL", "gpt-5.6-terra") or "gpt-5.6-terra"
        self.llm_timeout_seconds = _env_int("LLM_TIMEOUT_SECONDS", 240)

        # --- Local embeddings (Sentence Transformers) ---
        self.embedding_model = _env("EMBEDDING_MODEL", "all-MiniLM-L6-v2") or "all-MiniLM-L6-v2"
        self.embedding_device = _env("EMBEDDING_DEVICE", "cpu") or "cpu"
        self.embedding_batch_size = _env_int("EMBEDDING_BATCH_SIZE", 32)

        # --- RAG tuning ---
        self.chunk_size = _env_int("CHUNK_SIZE", 1000)
        self.chunk_overlap = _env_int("CHUNK_OVERLAP", 150)
        self.top_k = _env_int("TOP_K", 5)
        self.min_similarity = float(_env("MIN_SIMILARITY", "0.08") or "0.08")

        # --- CORS ---
        cors = _env("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        self.cors_origins = [o.strip() for o in cors.split(",") if o.strip()]

        # --- Misc ---
        self.allowed_pdf_extensions = (".pdf",)


_load_env_file()

settings = Settings()
