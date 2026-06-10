"""Tests de la mezcla prior↔aprendido (shrinkage): el peso crece con los partidos jugados."""

from app.model.blend import blend_weight, team_strength
from app.model.strength import attack_defense


def test_peso_crece_con_partidos():
    assert blend_weight(0) == 0.0
    assert blend_weight(1) < blend_weight(3) < blend_weight(10)
    assert blend_weight(1000) > 0.99


def test_sin_datos_devuelve_prior():
    # learned vacío → fuerza = prior FIFA puro.
    prior = attack_defense("Spain")
    out = team_strength("Spain", learned={})
    assert out["weight"] == 0.0
    assert out["attack"] == prior["attack"]
    assert out["defense"] == prior["defense"]


def test_mezcla_se_acerca_a_lo_aprendido_con_muchos_partidos():
    prior = attack_defense("Japan")
    learned = {"japan": {"attack": 1.5, "defense": 0.5, "games": 50}}
    out = team_strength("Japan", learned)
    # Con 50 partidos, la fuerza final debe estar mucho más cerca de lo aprendido que del prior.
    assert abs(out["attack"] - 1.5) < abs(out["attack"] - prior["attack"])
    assert out["weight"] > 0.9
