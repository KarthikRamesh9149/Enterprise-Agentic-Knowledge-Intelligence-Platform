from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "Enterprise Agentic Knowledge Intelligence Platform"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/knowledge"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "local-dev-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440
    upload_dir: str = "/app/uploads"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    embedding_provider: str = "mock"
    embedding_dimension: int = 128
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    llm_provider: str = "mock"
    openai_chat_model: str = "gpt-5-mini"
    llm_temperature: float = 0.1
    max_output_tokens: int = 1200
    openai_reasoning_effort: str = "minimal"
    openai_text_verbosity: str = "low"
    rag_top_k: int = 8
    rag_max_context_chars: int = 12000
    citation_max_chars: int = 360
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    rate_limit_per_minute: int = 60
    frontend_url: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
