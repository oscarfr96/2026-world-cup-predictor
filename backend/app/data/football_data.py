"""Cliente de football-data.org (v4) — la ÚNICA fuente externa del proyecto.

Es gratis (10 req/min) y la única que cubre el Mundial 2026: 104 partidos con fecha, estado y, una
vez jugados, el marcador. La usamos para:
  - el CALENDARIO completo (todas las jornadas, de la fase de grupos a la final), y
  - los RESULTADOS reales (para entrenar el GLM y marcar acierto/fallo).

Solo se llama dentro de /admin/recompute (1 vez al día). El frontend NUNCA la toca.
"""

from __future__ import annotations

import httpx

WC_CODE = "WC"  # FIFA World Cup en football-data.org

# Orden de las fases para presentar las jornadas (de grupos a la final). Las claves son los `stage`
# de football-data.org; el valor es el orden y una etiqueta legible en español.
STAGE_ORDER: dict[str, tuple[int, str]] = {
    "GROUP_STAGE": (0, "Fase de grupos"),
    "LAST_32": (1, "Dieciseisavos"),
    "LAST_16": (2, "Octavos"),
    "QUARTER_FINALS": (3, "Cuartos"),
    "SEMI_FINALS": (4, "Semifinales"),
    "THIRD_PLACE": (5, "Tercer puesto"),
    "FINAL": (6, "Final"),
}


class FootballDataError(RuntimeError):
    pass


class FootballData:
    def __init__(self, key: str, base: str = "https://api.football-data.org/v4", timeout: float = 25.0):
        if not key:
            raise FootballDataError("Falta FOOTBALL_DATA_ORG_KEY en el entorno del backend.")
        self._client = httpx.Client(base_url=base, headers={"X-Auth-Token": key}, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FootballData":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def matches(self, code: str = WC_CODE) -> list[dict]:
        """Todos los partidos del torneo, normalizados.

        Cada partido: {utcDate, status, home, away, matchday, stage, home_goals, away_goals}.
        `home_goals`/`away_goals` son None hasta que el partido termina (status == FINISHED).
        """
        r = self._client.get(f"/competitions/{code}/matches")
        if r.status_code != 200:
            raise FootballDataError(f"football-data /matches → HTTP {r.status_code}: {r.text[:200]}")

        out: list[dict] = []
        for m in r.json().get("matches", []):
            score = (m.get("score") or {}).get("fullTime") or {}
            out.append({
                "id": m.get("id"),          # id estable del partido (para casar predicción ↔ resultado)
                "utcDate": m.get("utcDate"),
                "status": m.get("status"),
                "home": (m.get("homeTeam") or {}).get("name"),
                "away": (m.get("awayTeam") or {}).get("name"),
                "matchday": m.get("matchday"),
                "stage": m.get("stage"),
                "home_goals": score.get("home"),
                "away_goals": score.get("away"),
            })
        return out


def finished_results(matches: list[dict]) -> list[dict]:
    """Solo los partidos ya jugados con marcador (para entrenar el GLM en fase 2)."""
    return [
        m for m in matches
        if m.get("status") == "FINISHED" and m.get("home_goals") is not None and m.get("away_goals") is not None
    ]


def group_into_rounds(matches: list[dict]) -> list[dict]:
    """Agrupa los partidos en jornadas ordenadas (fase de grupos → final).

    Una "jornada" = un (stage, matchday). Devuelve:
        [ {stage, stage_label, matchday, key, matches: [...] }, ... ]  ordenado para la web.
    Incluye las eliminatorias aunque aún no tengan equipos (vienen con fecha pero sin selecciones);
    se mostrarán como rondas "pendientes" hasta que se conozcan los cruces.
    """
    buckets: dict[tuple, list[dict]] = {}
    for m in matches:
        key = (m.get("stage") or "", m.get("matchday"))
        buckets.setdefault(key, []).append(m)

    rounds: list[dict] = []
    for (stage, matchday), ms in buckets.items():
        order, label = STAGE_ORDER.get(stage, (99, stage or "Otra fase"))
        ms_sorted = sorted(ms, key=lambda x: x.get("utcDate") or "")
        rounds.append({
            "stage": stage,
            "stage_label": label,
            "matchday": matchday,
            # clave estable para el frontend (p.ej. "GROUP_STAGE-1", "FINAL-None")
            "key": f"{stage}-{matchday}",
            "sort": (order, matchday or 0, ms_sorted[0].get("utcDate") or ""),
            "matches": ms_sorted,
        })

    rounds.sort(key=lambda r: r["sort"])
    for r in rounds:
        r.pop("sort", None)
    return rounds
