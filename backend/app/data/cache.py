"""Caché de predicciones en disco (`data/predictions.json`) + guard diario.

Es la pieza que protege la API gratuita: el cálculo caro (que llama a football-data.org) se hace
UNA vez al día y se guarda aquí; el endpoint público `/predictions` solo lee este fichero. Aunque
entren 1000 personas, son 1000 lecturas de un JSON, cero llamadas externas.

El disco de Render free es efímero (se borra al redesplegar). Por eso `predictions.json` se commitea
como semilla y la app lo lee al arrancar; el cron lo refresca en runtime.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import tempfile


def _today() -> str:
    return dt.date.today().isoformat()


def read_cache(path: str) -> dict | None:
    """Lee el snapshot de predicciones. Devuelve None si no existe o está corrupto."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(path: str, snapshot: dict) -> None:
    """Escribe el snapshot de forma atómica (escribe a temporal y renombra) para no dejar JSON a medias."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def already_computed_today(path: str) -> bool:
    """True si la caché ya se generó HOY (mismo día UTC local).

    Es el segundo cerrojo (además del token): aunque disparen /admin/recompute mil veces en un día,
    solo la primera toca football-data.org; el resto devuelve la caché existente.
    """
    cache = read_cache(path)
    if not cache:
        return False
    return cache.get("computed_date") == _today()


def stamp_today() -> str:
    """Fecha (ISO) para sellar el snapshot recién generado."""
    return _today()
