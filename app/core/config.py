"""
Application configuration loaded from environment variables via Pydantic BaseSettings.

WAN-aware CORS origins are supplied through ALLOWED_ORIGINS (comma-separated).
Use ``*`` in development to accept ngrok tunnel URLs and remote frontend origins.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for MediVault AI backend services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="MediVault AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # CORS — WAN-aware dynamic origins
    allowed_origins_raw: str = Field(default="*", alias="ALLOWED_ORIGINS")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Redis / Celery
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND"
    )

    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # File storage
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_path: str = Field(default="./storage", alias="STORAGE_LOCAL_PATH")
    storage_max_file_size_mb: int = Field(default=25, alias="STORAGE_MAX_FILE_SIZE_MB")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket: str = Field(default="", alias="AWS_S3_BUCKET")
    aws_s3_region: str = Field(default="us-east-1", alias="AWS_S3_REGION")

    # LLM
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    whisper_model: str = Field(default="whisper-large-v3", alias="WHISPER_MODEL")

    # ChromaDB / embeddings
    chroma_persist_dir: str = Field(default="./chroma_data", alias="CHROMA_PERSIST_DIR")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")

    # Tunnel
    tunnel_url_file: str = Field(default=".tunnel_url", alias="TUNNEL_URL_FILE")

    # Rate limiting
    auth_rate_limit: str = Field(default="10/minute", alias="AUTH_RATE_LIMIT")

    @property
    def allowed_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list; ``*`` permits all origins."""
        raw = self.allowed_origins_raw.strip()
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        """Maximum upload size in bytes derived from megabyte setting."""
        return self.storage_max_file_size_mb * 1024 * 1024

    @field_validator("secret_key", "jwt_secret_key")
    @classmethod
    def validate_secret_length(cls, value: str) -> str:
        """Ensure cryptographic secrets meet minimum entropy requirements."""
        if len(value) < 32:
            raise ValueError("Secret keys must be at least 32 characters long")
        return value

    @property
    def is_production(self) -> bool:
        """True when running in production environment."""
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
