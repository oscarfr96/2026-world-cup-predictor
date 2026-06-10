"""Orquestación del recompute (lo caro, 1 vez al día): datos → modelo → predicciones → caché.

Pasos:
  1. Traer todos los partidos del Mundial de football-data.org (calendario + marcadores).
  2. FASE 2: si hay suficientes partidos jugados, entrenar el GLM de Poisson (train.py). Si no, {}.
  3. Para cada partido (de cada jornada), calcular la fuerza de cada selección = mezcla prior↔GLM
     (blend.py) → goles esperados → predicción (poisson.py).
  4. En los partidos ya jugados, comparar la predicción con el resultado real → acierto/fallo.
  5. Empaquetar todo en un snapshot y guardarlo en la caché.

La frontera está limpia: este módulo NO sabe nada de HTTP/usuarios; main.py lo invoca y persiste.
"""

from __future__ import annotations

import datetime as dt

from .data.cache import stamp_today
from .data.football_data import (
    FootballData,
    WC_CODE,
    finished_results,
    group_into_rounds,
)
from .model.blend import team_strength
from .model.poisson import HOME_ADVANTAGE, expected_goals_for, predict_from_lambdas
from .model.strength import is_host_nation
from .model.train import train_strength


def _actual_result(home_goals: int, away_goals: int) -> str:
    """Resultado real de un partido en la misma escala que el predicho ('home'|'draw'|'away')."""
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"


def _predict_match(match: dict, learned: dict[str, dict]) -> dict:
    """Predicción de un partido + (si ya se jugó) resultado real y flag de acierto."""
    home, away = match["home"], match["away"]

    hs = team_strength(home, learned)
    as_ = team_strength(away, learned)

    # Goles esperados: ataque propio × defensa rival. La ventaja de campo solo se aplica si el "local"
    # es una selección anfitriona (juega en su país); el resto del Mundial es en sede neutral.
    home_factor = HOME_ADVANTAGE if is_host_nation(home) else 1.0
    lam_h = expected_goals_for(hs["attack"], as_["defense"]) * home_factor
    lam_a = expected_goals_for(as_["attack"], hs["defense"])

    pred = predict_from_lambdas(home, away, lam_h, lam_a)

    # Cuánto pesa lo aprendido en este partido (0 = pura heurística). Útil para explicarlo en la web.
    pred["learned_weight"] = round(max(hs["weight"], as_["weight"]), 3)
    pred["id"] = match.get("id")
    pred["utcDate"] = match.get("utcDate")
    pred["status"] = match.get("status")
    pred["pending"] = False

    played = match.get("status") == "FINISHED" and match.get("home_goals") is not None
    if played:
        hg, ag = int(match["home_goals"]), int(match["away_goals"])
        actual = _actual_result(hg, ag)
        pred["played"] = True
        pred["real_score"] = f"{hg}-{ag}"
        pred["real_result"] = actual
        pred["correct"] = (pred["winner"] == actual)
    else:
        pred["played"] = False
    return pred


def _pending_match(match: dict) -> dict:
    """Partido de eliminatoria aún sin equipos: se muestra como 'pendiente' (sin predicción)."""
    return {
        "pending": True,
        "played": False,
        "utcDate": match.get("utcDate"),
        "status": match.get("status"),
    }


def build_snapshot(matches: list[dict]) -> dict:
    """Construye el snapshot completo de predicciones a partir de los partidos crudos."""
    results = finished_results(matches)
    learned = train_strength(results)        # {} si todavía estamos en fase 1 (heurística)

    rounds_raw = group_into_rounds(matches)
    rounds: list[dict] = []
    n_correct = n_played = 0

    for r in rounds_raw:
        preds = []
        for m in r["matches"]:
            # Con equipos → se predice; sin equipos (cruce por decidir) → placeholder pendiente.
            if m.get("home") and m.get("away"):
                preds.append(_predict_match(m, learned))
            else:
                preds.append(_pending_match(m))
        for p in preds:
            if p["played"]:
                n_played += 1
                n_correct += int(p["correct"])
        rounds.append({
            "stage": r["stage"],
            "stage_label": r["stage_label"],
            "matchday": r["matchday"],
            "key": r["key"],
            "pending": all(p["pending"] for p in preds),   # ronda entera por definir
            "matches": preds,
        })

    # "pretrained" = prior aprendido de partidos internacionales (sin cold start);
    # "trained" = ya incorpora además los resultados del propio Mundial.
    phase = "trained" if learned else "pretrained"
    return {
        "computed_date": stamp_today(),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "phase": phase,                       # "heuristic" (fase 1) | "trained" (fase 2)
        "matches_played": len(results),       # partidos del Mundial ya jugados
        "teams_learned": len(learned),        # selecciones con fuerza aprendida por el GLM
        "accuracy": {
            "correct": n_correct,
            "evaluated": n_played,
            "pct": round(100 * n_correct / n_played, 1) if n_played else None,
        },
        "rounds": rounds,
    }


def recompute(api_key: str) -> dict:
    """Trae los datos del día y devuelve el snapshot. Aquí (y solo aquí) se llama a la API externa."""
    with FootballData(api_key) as fd:
        matches = fd.matches(WC_CODE)
    return build_snapshot(matches)
