"""FASE 2 (modelo entrenado): regresión de Poisson sobre los goles reales del Mundial.

Este es el salto heurística → ML del proyecto. En cuanto se juegan partidos, en vez de fiarnos solo
de la tabla FIFA, APRENDEMOS la fuerza de cada selección de los goles que de verdad ha marcado y
encajado.

EL MODELO (clásico de fútbol, Maher 1982): cada partido aporta DOS filas, una por equipo:

    goles | equipo (ataca) | rival (defiende) | local?
    ------+----------------+------------------+-------
      2   | Spain          | Croatia          |  1
      0   | Croatia        | Spain            |  0

Ajustamos un GLM de familia Poisson:   log(goles_esperados) = µ + ataque[equipo] + defensa[rival] + β·local
Los coeficientes ajustados SON la fuerza aprendida:
  - ataque[equipo] alto  → ese equipo marca mucho.
  - defensa[rival] alto  → contra ese rival se marca mucho → su defensa es DÉBIL (encaja).

Convertimos esos coeficientes en multiplicadores centrados en 1.0 (misma escala que el prior FIFA en
strength.py), para que el resto del modelo (poisson.expected_goals_for) no tenga que cambiar nada.
La mezcla con el prior, para no fiarnos de 2 partidos, se hace en blend.py.
"""

from __future__ import annotations

import numpy as np

from .strength import normalize_name

# Mínimo de partidos jugados para intentar entrenar. Con muy pocos, el ajuste no aporta y puede
# dar coeficientes disparatados (separación perfecta); por debajo de esto usamos solo el prior.
MIN_MATCHES_TO_TRAIN = 8

# Acotamos los multiplicadores aprendidos al mismo rango que el prior, para que un resultado
# extremo (un 7-0 puntual) no dispare la fuerza estimada.
_MULT_MIN, _MULT_MAX = 0.5, 1.5


def _rows_from_results(results: list[dict]) -> list[dict]:
    """Convierte partidos jugados en filas (una por equipo) para el GLM.

    `results` = [{home, away, home_goals, away_goals}, ...] (solo partidos FINISHED).
    """
    rows: list[dict] = []
    for m in results:
        h, a = normalize_name(m["home"]), normalize_name(m["away"])
        hg, ag = m.get("home_goals"), m.get("away_goals")
        if hg is None or ag is None:
            continue
        rows.append({"goals": int(hg), "team": h, "opp": a, "home": 1})
        rows.append({"goals": int(ag), "team": a, "opp": h, "home": 0})
    return rows


def train_strength(results: list[dict]) -> dict[str, dict]:
    """Entrena el GLM de Poisson y devuelve la fuerza APRENDIDA por selección.

    Salida: { team_norm: {"attack": mult, "defense": mult, "games": n} }  (vacío si no se entrena).
    `attack`/`defense` son multiplicadores centrados en 1.0, listos para expected_goals_for.

    Se importa statsmodels/pandas DENTRO de la función para que el resto del backend arranque aunque
    no estén instalados (p.ej. en un primer despliegue antes de la fase 2).
    """
    rows = _rows_from_results(results)
    n_matches = len(rows) // 2
    if n_matches < MIN_MATCHES_TO_TRAIN:
        return {}  # todavía pocos datos → el pipeline se queda con el prior FIFA

    import pandas as pd
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    df = pd.DataFrame(rows)

    # GLM Poisson: goles ~ ataque(equipo) + defensa(rival) + ventaja de local.
    # C(...) trata equipo y rival como variables categóricas (un coeficiente por selección).
    try:
        model = smf.glm(
            "goals ~ C(team) + C(opp) + home", data=df, family=sm.families.Poisson()
        ).fit()
    except Exception as exc:  # noqa: BLE001 — si no converge, nos quedamos con el prior
        print(f"[train] El GLM no convergió ({exc}); se usa solo el prior.")
        return {}

    params = model.params

    # Partidos jugados por selección (para el shrinkage por equipo en blend.py).
    games: dict[str, int] = {}
    for r in rows:
        games[r["team"]] = games.get(r["team"], 0) + 1

    teams = sorted(games.keys())

    # Efecto de ataque y de defensa por selección (en escala log). El coeficiente de la categoría de
    # referencia (la que statsmodels omite) es 0; el resto, relativo a ella.
    def attack_effect(t: str) -> float:
        return float(params.get(f"C(team)[T.{t}]", 0.0))

    def defense_effect(t: str) -> float:
        return float(params.get(f"C(opp)[T.{t}]", 0.0))

    # Centramos en la media (en log) y exponenciamos → multiplicador centrado en 1.0.
    mean_atk = np.mean([attack_effect(t) for t in teams])
    mean_def = np.mean([defense_effect(t) for t in teams])

    def _mult(effect: float, mean: float) -> float:
        return float(np.clip(np.exp(effect - mean), _MULT_MIN, _MULT_MAX))

    learned: dict[str, dict] = {}
    for t in teams:
        learned[t] = {
            "attack": round(_mult(attack_effect(t), mean_atk), 3),
            "defense": round(_mult(defense_effect(t), mean_def), 3),
            "games": games[t],  # nº de partidos jugados por la selección
        }
    return learned
