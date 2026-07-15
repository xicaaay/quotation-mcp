"""Configuración central del servidor MCP."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables requeridas para ejecutar el servidor de lectura."""

    database_url: str = Field(alias="DATABASE_URL")
    max_results: int = Field(default=50, alias="MCP_MAX_RESULTS", ge=1, le=200)
    database_connect_timeout: int = Field(
        default=10,
        alias="MCP_DATABASE_CONNECT_TIMEOUT",
        ge=1,
        le=60,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Carga una única instancia validada de la configuración."""

    return Settings()
