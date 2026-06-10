"""API pública del predictor del Mundial 2026.

Separa COMPUTE de READ para no saturar la API gratuita de fútbol:
  - GET  /predictions     → barato, ilimitado. Sirve la caché. NUNCA llama a football-data.org.
  - POST /admin/recompute → caro, 1 vez/día. Protegido por token + guard de fecha. Lo dispara el cron.
  - GET  /health          → liveness.

Así 1000 visitas = 1000 lecturas de un JSON; la única llamada externa la hace el cron una vez al día.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import get_settings
from .data import cache
from .pipeline import recompute as run_recompute

app = FastAPI(title="2026 World Cup Predictor", version="0.1.0")

# Rate limit por IP. /predictions es público y solo lee un fichero, pero sin límite un solo cliente
# podría machacarlo y tumbar el Render free; esto corta los abusos básicos sin afectar a un usuario
# normal. La IP real la da X-Forwarded-For (uvicorn arranca con --proxy-headers en Render); en local,
# sin proxy, get_remote_address usa la IP directa.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Respuesta 429 clara cuando se supera el límite (en vez del HTML por defecto)."""
    return JSONResponse(
        content={"detail": "Demasiadas peticiones. Espera un momento y vuelve a intentarlo."},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_settings.ALLOWED_ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Liveness. Responde siempre, aunque falten las claves (degradación elegante)."""
    return {"status": "ok"}


@app.get("/predictions")
@limiter.limit("60/minute")
def predictions(request: Request) -> dict:
    """Devuelve el último snapshot de predicciones (solo lectura, sin tocar la API externa).

    Limitado a 60 peticiones/minuto por IP: de sobra para un usuario real (la web hace 1 por carga),
    pero corta a quien intente machacar el endpoint.
    """
    settings = get_settings()
    snapshot = cache.read_cache(settings.CACHE_PATH)
    if snapshot is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Aún no hay predicciones generadas. El recompute diario las creará.",
        )
    return snapshot


def _require_token(x_recompute_token: str = Header(default="")) -> None:
    """Comprueba el token del recompute. Sin token configurado o incorrecto → 401/403."""
    settings = get_settings()
    if not settings.RECOMPUTE_TOKEN:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "RECOMPUTE_TOKEN no configurado en el servidor.")
    if x_recompute_token != settings.RECOMPUTE_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token de recompute inválido.")


@app.post("/admin/recompute")
def admin_recompute(force: bool = False, _: None = Depends(_require_token)) -> dict:
    """Recalcula las predicciones del día y actualiza la caché.

    - Guard de fecha: si ya se calculó hoy y no se fuerza, devuelve la caché SIN llamar a la API.
    - `force=true` ignora el guard (úsalo con cuidado: gasta una llamada a la API).
    """
    settings = get_settings()

    if not force and cache.already_computed_today(settings.CACHE_PATH):
        return {"status": "cached", **(cache.read_cache(settings.CACHE_PATH) or {})}

    if not settings.FOOTBALL_DATA_ORG_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "FOOTBALL_DATA_ORG_KEY no configurada.")

    try:
        snapshot = run_recompute(settings.FOOTBALL_DATA_ORG_KEY)
    except Exception as exc:  # noqa: BLE001 — error de la fuente externa → 502 con mensaje claro
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Fuente de datos: {exc}")

    cache.write_cache(settings.CACHE_PATH, snapshot)
    return {"status": "recomputed", **snapshot}
