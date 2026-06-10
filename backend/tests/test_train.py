"""Test de la fase 2: con suficientes partidos jugados, el GLM de Poisson entrena.

Construimos una liguilla simulada donde 'Alpha' arrasa y 'Delta' pierde siempre, y comprobamos que
el modelo aprende a Alpha con más ataque que Delta. Requiere statsmodels (dependencia de fase 2).
"""

import pytest

from app.model.train import MIN_MATCHES_TO_TRAIN, train_strength

pytest.importorskip("statsmodels")


def _league() -> list[dict]:
    """Doble liguilla de 4 equipos (12 partidos) con un patrón claro de fuerza."""
    teams = ["Alpha", "Beta", "Gamma", "Delta"]
    goals = {  # goles que marca cada equipo según el rival (patrón: Alpha fuerte, Delta flojo)
        ("Alpha", "Beta"): 3, ("Alpha", "Gamma"): 4, ("Alpha", "Delta"): 5,
        ("Beta", "Gamma"): 2, ("Beta", "Delta"): 3, ("Gamma", "Delta"): 2,
    }
    def g(a, b):
        if (a, b) in goals:
            return goals[(a, b)]
        return max(0, goals.get((b, a), 1) - 2)  # el más débil marca menos

    results = []
    for i, h in enumerate(teams):
        for a in teams[i + 1:]:
            results.append({"home": h, "away": a, "home_goals": g(h, a), "away_goals": g(a, h)})
            results.append({"home": a, "away": h, "home_goals": g(a, h), "away_goals": g(h, a)})
    return results


def test_glm_entrena_y_aprende_jerarquia():
    results = _league()
    assert len(results) >= MIN_MATCHES_TO_TRAIN
    learned = train_strength(results)
    assert learned, "el GLM debería haber entrenado con 12 partidos"
    assert learned["alpha"]["attack"] > learned["delta"]["attack"]
    # Multiplicadores acotados al rango del prior.
    for rec in learned.values():
        assert 0.5 <= rec["attack"] <= 1.5
        assert 0.5 <= rec["defense"] <= 1.5
