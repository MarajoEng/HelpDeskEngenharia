from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Portal de Chamados Engenharia API"
    app_env: str = "development"
    app_debug: bool = False
    api_prefix: str = ""
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/helpdesk_engenharia"
    )
    secret_key: str = "change-me-in-dev"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
