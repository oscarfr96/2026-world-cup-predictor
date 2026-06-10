"""Configuración del backend: variables de entorno (`.env`) — sin secretos en el repo.

Todo lo sensible (clave de la API de fútbol, token del recompute) vive SOLO en variables de
entorno: en local en `.env` (gitignored), en producción en el panel de Render. El código arranca
aunque falten (degradación elegante): `/health` siempre responde y `/predictions` sirve la caché.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Clave de football-data.org (gratis, 10 req/min). Solo se usa en /admin/recompute.
    FOOTBALL_DATA_ORG_KEY: str = ""

    # Token que protege /admin/recompute (lo conoce solo el cron job de Render).
    RECOMPUTE_TOKEN: str = ""

    # CORS: URL del frontend.
    ALLOWED_ORIGIN: str = "http://localhost:5173"

    # Ruta del fichero de caché con las predicciones (relativa al backend).
    CACHE_PATH: str = "data/predictions.json"


@lru_cache
def get_settings() -> Settings:
    """Settings cacheado (se lee el .env una sola vez)."""
    return Settings()
