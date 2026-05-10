from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "SecureFrame Gallery"

    database_url: str = "sqlite:///./secureframe.db"
    secret_key: str = "change-me-only-for-local-development"
    algorithm: str = "HS256"

    access_token_expire_minutes: int = 120
    frontend_origin: str = "http://localhost:5173"
    upload_dir: str = "uploads"

    minio_url: str = "localhost:9393"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "change-this-minio-secret"
    minio_bucket_quarantine: str = "uploads-quarantine"
    minio_bucket_public: str = "gallery-public"
    minio_bucket_evidence: str = "rejected-evidence"

    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
