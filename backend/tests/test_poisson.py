"""Tests del núcleo Poisson (fase 1): el favorito y las probabilidades tienen sentido."""

from app.model.poisson import expected_goals_for, predict_from_lambdas, score_matrix
from app.model.strength import attack_defense


def test_score_matrix_suma_uno():
    m = score_matrix(1.4, 1.1, max_goals=8, rho=-0.05)
    assert abs(m.sum() - 1.0) < 1e-9


def test_1x2_suma_uno():
    pred = predict_from_lambdas("A", "B", 1.6, 0.9)
    o = pred["outcome"]
    assert abs(o["home"] + o["draw"] + o["away"] - 1.0) < 1e-6


def test_favorito_es_el_mas_fuerte():
    # Brasil (fuerte) en casa contra Curacao (débil) → favorito claro Brasil.
    hs = attack_defense("Brazil")
    aw = attack_defense("Curacao")
    lam_h = expected_goals_for(hs["attack"], aw["defense"]) * 1.1
    lam_a = expected_goals_for(aw["attack"], hs["defense"])
    pred = predict_from_lambdas("Brazil", "Curacao", lam_h, lam_a)
    assert pred["winner"] == "home"
    assert pred["favorite"] == "Brazil"
    assert pred["expected_goals"]["home"] > pred["expected_goals"]["away"]


def test_marcadores_top_ordenados():
    pred = predict_from_lambdas("A", "B", 1.5, 1.2, top_n=5)
    probs = [s["prob"] for s in pred["most_likely_scores"]]
    assert probs == sorted(probs, reverse=True)
    assert len(pred["most_likely_scores"]) == 5
