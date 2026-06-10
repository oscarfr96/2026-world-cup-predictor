"""Núcleo de predicción de un partido: modelo de Poisson ataque/defensa (+ Dixon-Coles).

La estadística clásica del fútbol (Maher 1982, Dixon-Coles 1997): los goles de cada equipo en un
partido se modelan como una Poisson cuya media λ ("goles esperados") depende de la fuerza ofensiva
del equipo y la defensiva del rival. Con las dos λ se construye una MATRIZ de marcadores
P(local=i, visitante=j) y de ahí salen el 1X2, el favorito y los marcadores más probables.

Esta es la FASE 1 (heurística): las λ vienen de la tabla de fuerza FIFA (strength.py). En la FASE 2
las mismas λ se calculan con la fuerza APRENDIDA por la regresión de Poisson; el resto no cambia.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import poisson

# Goles medios por equipo y partido en el torneo (ancla del modelo Poisson).
BASELINE_GOALS = 1.35

# Factor campo. Solo se aplica a las selecciones ANFITRIONAS (juegan en su país); el pipeline decide
# a quién, ver is_host_nation en strength.py. 1.0 = sin ventaja de local. Editable.
HOME_ADVANTAGE = 1.10


def expected_goals_for(team_attack: float, opp_defense: float, baseline: float = BASELINE_GOALS) -> float:
    """Goles esperados (λ) de un equipo en el partido.

    `team_attack` > 1 → ataque fuerte; `opp_defense` > 1 → defensa rival débil (encaja más).
    """
    return baseline * team_attack * opp_defense


def _dixon_coles_tau(i: int, j: int, lam_h: float, lam_a: float, rho: float) -> float:
    """Corrección Dixon-Coles para los marcadores bajos (0-0, 1-0, 0-1, 1-1).

    El Poisson independiente sobreestima un poco los empates y subestima 0-0/1-1. `rho` ajusta esas
    cuatro celdas; rho<0 (lo habitual) sube 0-0/1-1 y baja 1-0/0-1. El resto de celdas, τ=1.
    """
    if i == 0 and j == 0:
        return 1.0 - lam_h * lam_a * rho
    if i == 0 and j == 1:
        return 1.0 + lam_h * rho
    if i == 1 and j == 0:
        return 1.0 + lam_a * rho
    if i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(lam_h: float, lam_a: float, *, max_goals: int = 8, rho: float = 0.0) -> np.ndarray:
    """Matriz (max_goals+1)×(max_goals+1) con P(local=i, visitante=j), normalizada.

    Con `rho=0` es un Poisson independiente puro; con `rho<0` aplica la corrección Dixon-Coles a los
    cuatro marcadores bajos. Se renormaliza para repartir la cola truncada en max_goals.
    """
    ph = poisson.pmf(np.arange(max_goals + 1), lam_h)
    pa = poisson.pmf(np.arange(max_goals + 1), lam_a)
    matrix = np.outer(ph, pa)

    if rho != 0.0:
        for i in (0, 1):
            for j in (0, 1):
                matrix[i, j] *= _dixon_coles_tau(i, j, lam_h, lam_a, rho)

    total = matrix.sum()
    return matrix / total if total > 0 else matrix


def most_likely_score_for(matrix: np.ndarray, result: str, max_goals: int) -> dict:
    """Marcador exacto más probable consistente con `result` ('home' | 'draw' | 'away')."""
    best: dict | None = None
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            if result == "home" and not i > j:
                continue
            if result == "away" and not i < j:
                continue
            if result == "draw" and i != j:
                continue
            p = float(matrix[i, j])
            if best is None or p > best["prob"]:
                best = {"score": f"{i}-{j}", "prob": round(p, 4)}
    return best or {"score": "0-0", "prob": 0.0}


def predict_from_lambdas(
    home: str,
    away: str,
    lam_h: float,
    lam_a: float,
    *,
    max_goals: int = 8,
    rho: float = -0.05,
    top_n: int = 5,
) -> dict:
    """Predice un partido a partir de las dos λ ya calculadas. Devuelve un dict listo para la API.

    Separa el cálculo de λ (que cambia entre fase 1 y fase 2) de la conversión λ → resultado (común).
    `rho` < 0 activa Dixon-Coles. Salida: favorito, goles esperados, 1X2, marcadores más probables.
    """
    matrix = score_matrix(lam_h, lam_a, max_goals=max_goals, rho=rho)

    p_home = float(np.tril(matrix, -1).sum())  # i > j → gana local
    p_draw = float(np.trace(matrix))           # i == j → empate
    p_away = float(np.triu(matrix, 1).sum())   # i < j → gana visitante

    scores = [
        {"score": f"{i}-{j}", "prob": round(float(matrix[i, j]), 4)}
        for i in range(max_goals + 1)
        for j in range(max_goals + 1)
    ]
    top = sorted(scores, key=lambda s: s["prob"], reverse=True)[:top_n]

    outcome = {"home": p_home, "draw": p_draw, "away": p_away}
    winner = max(outcome, key=outcome.get)  # 'home' | 'draw' | 'away'

    return {
        "home": home,
        "away": away,
        "expected_goals": {"home": round(lam_h, 2), "away": round(lam_a, 2)},
        "outcome": {k: round(v, 3) for k, v in outcome.items()},
        "winner": winner,
        # Nombre del equipo favorito (o "Empate"), cómodo para la web.
        "favorite": {"home": home, "away": away, "draw": "Empate"}[winner],
        # El marcador exacto más probable ENTRE los consistentes con el resultado más probable.
        # (El marcador global suele ser 1-1/0-0 aunque haya claro favorito; condicionarlo despista menos.)
        "likely_score": most_likely_score_for(matrix, winner, max_goals),
        "most_likely_scores": top,
    }
