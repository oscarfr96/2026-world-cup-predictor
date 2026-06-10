"""Mezcla del prior FIFA (fase 1) con la fuerza aprendida por el GLM (fase 2) — shrinkage.

EL PROBLEMA: en un Mundial cada selección juega poquísimo (3 partidos en la fase de grupos). Fiarse
de la regresión de Poisson con 1-2 partidos es temerario: un 3-0 puntual no convierte a nadie en
favorito. Pero ignorar lo que ya ha pasado tampoco tiene sentido.

LA SOLUCIÓN (shrinkage, la misma idea bayesiana de toda la vida): la fuerza final de cada selección
es una media ponderada entre su prior (FIFA) y lo aprendido (GLM), donde el peso de lo aprendido
CRECE con el número de partidos jugados:

    peso = n / (n + k)        # n = partidos jugados por la selección, k = "partidos virtuales" del prior

Al principio del torneo (n pequeño) → manda el prior. Al final (n grande) → mandan los datos. `k` es
el dial que controla cómo de rápido confiamos en lo observado.
"""

from __future__ import annotations

from .strength import attack_defense, normalize_name

# "Partidos virtuales" que vale el prior. k alto = tardamos más en fiarnos de los datos del Mundial
# (sensato: las muestras son pequeñas y ruidosas).
PSEUDO_COUNT = 3.0


def blend_weight(games: float, pseudo_count: float = PSEUDO_COUNT) -> float:
    """Peso (0..1) que damos a lo APRENDIDO frente al prior, según partidos jugados."""
    denom = games + pseudo_count
    return games / denom if denom > 0 else 0.0


def team_strength(team_name: str, learned: dict[str, dict], pseudo_count: float = PSEUDO_COUNT) -> dict:
    """Fuerza ataque/defensa final de una selección = mezcla(prior FIFA, GLM aprendido).

    `learned` = salida de train.train_strength ({} si aún no se entrena → devuelve el prior puro).
    Devuelve {"attack", "defense", "weight", "games"} para que el pipeline/UI puedan explicar la mezcla.
    """
    prior = attack_defense(team_name)
    rec = learned.get(normalize_name(team_name))

    if not rec:
        # Sin datos aprendidos para esta selección → prior puro (fase 1).
        return {"attack": prior["attack"], "defense": prior["defense"], "weight": 0.0, "games": 0}

    w = blend_weight(rec.get("games", 0), pseudo_count)
    attack = (1.0 - w) * prior["attack"] + w * rec["attack"]
    defense = (1.0 - w) * prior["defense"] + w * rec["defense"]
    return {
        "attack": round(attack, 3),
        "defense": round(defense, 3),
        "weight": round(w, 3),       # cuánto pesa lo aprendido (0 = solo prior, 1 = solo datos)
        "games": rec.get("games", 0),
    }
