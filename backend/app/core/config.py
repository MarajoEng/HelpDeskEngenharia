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
    max_upload_size_mb: int = 10
    upload_dir: str = "uploads"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    sla_monitor_lookback_days: int = 30
    sla_alert_repeat_hours: int = 6
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300
    report_export_max_rows: int = 5000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
