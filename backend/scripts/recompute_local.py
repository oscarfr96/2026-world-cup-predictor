"""Genera `data/predictions.json` en local, sin levantar el servidor.

Útil para: probar el modelo, refrescar la semilla que se commitea, o ver la salida antes de grabar.
Lee la clave de la API desde el `.env` del backend (igual que el servicio).

Uso (desde la carpeta backend, con el venv activado):
    python -m scripts.recompute_local
"""

from __future__ import annotations

import json

from app.config import get_settings
from app.data.cache import write_cache
from app.pipeline import recompute


def main() -> None:
    settings = get_settings()
    if not settings.FOOTBALL_DATA_ORG_KEY:
        raise SystemExit("Falta FOOTBALL_DATA_ORG_KEY en backend/.env")

    snapshot = recompute(settings.FOOTBALL_DATA_ORG_KEY)
    write_cache(settings.CACHE_PATH, snapshot)

    acc = snapshot["accuracy"]
    print(f"OK · fase={snapshot['phase']} · jugados={snapshot['matches_played']} "
          f"· jornadas={len(snapshot['rounds'])} · acierto={acc['pct']}% ({acc['correct']}/{acc['evaluated']})")
    print(f"Escrito en {settings.CACHE_PATH}")
    # Pequeña muestra para inspección rápida.
    if snapshot["rounds"]:
        print(json.dumps(snapshot["rounds"][0]["matches"][0], ensure_ascii=False, indent=2)[:600])


if __name__ == "__main__":
    main()
