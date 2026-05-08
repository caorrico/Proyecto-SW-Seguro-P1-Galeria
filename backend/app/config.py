from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "SecureFrame Gallery"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./secureframe.db"

    # JWT Security
    secret_key: str = "CHANGE_ME_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # File Upload
    upload_dir: str = "uploads"
    max_file_size_mb: int = 5

    # Rate Limiting
    rate_limit_login: str = "5/minute"

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — importar esto en toda la app."""
    return Settings()
