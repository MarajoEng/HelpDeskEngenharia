from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_debug: bool
    api_prefix: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Portal de Chamados Engenharia API"),
        app_env=os.getenv("APP_ENV", "development"),
        app_debug=_as_bool(os.getenv("APP_DEBUG"), default=False),
        api_prefix=os.getenv("API_PREFIX", ""),
    )
