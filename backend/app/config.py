from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "SecureFrame Gallery"

    database_url: str
    secret_key: str
    algorithm: str = "HS256"

    access_token_expire_minutes: int = 120
    frontend_origin: str = "http://localhost:5173"
    upload_dir: str = "uploads"

    minio_url: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_quarantine: str = "uploads-quarantine"
    minio_bucket_public: str = "gallery-public"
    minio_bucket_evidence: str = "rejected-evidence"

    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
