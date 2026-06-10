"""Genera el PRIOR objetivo de fuerza de cada selección a partir de resultados internacionales reales.

Sustituye la antigua tabla `_STRENGTH` hecha a mano por un rating aprendido de datos: pre-entrena el
mismo GLM de Poisson (ataque/defensa) que usamos en el torneo, pero sobre TODOS los partidos
internacionales recientes (clasificación, Nations League, amistosos…), con peso por recencia. Así el
modelo llega al Mundial "caliente" (no es un cold start) y el prior es objetivo, no a ojo.

Fuente: dataset abierto martj42/international_results (CSV, MIT, sin límites de API).

Uso (desde backend/, con el venv):  python -m scripts.build_prior
Escribe: app/model/international_ratings.json  (se commitea; se sirve como prior en strength.py)

No se ejecuta en producción: es un artefacto que se genera de vez en cuando y se versiona.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from app.model.strength import normalize_name

CSV_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"

# Ventana de datos y vida media del peso por recencia (un partido de hace HALF_LIFE años pesa la mitad).
YEARS_WINDOW = 6
HALF_LIFE_YEARS = 3.0

# Estabilidad numérica del GLM (con ~280 selecciones, las minúsculas causan separación/divergencia):
#   - agrupamos en "Other" las que tengan menos de MIN_GAMES partidos en la ventana,
#   - y acotamos goles extremos para que un 9-0 puntual no tenga un peso desmedido.
MIN_GAMES = 15
GOAL_CAP = 7

# Mismo recorte de multiplicadores que en el resto del modelo, para que un 7-0 puntual no dispare nada.
_MULT_MIN, _MULT_MAX = 0.5, 1.5

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "model", "international_ratings.json")

# Los 48 del Mundial 2026 en grafía football-data → grafía martj42 (solo los que difieren).
ALIAS_FD_TO_MARTJ42 = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "Czechia": "Czech Republic",
}


def _wc_team_names() -> list[str]:
    """Nombres (football-data) de las 48 selecciones, leídos de la caché de predicciones."""
    cache = os.path.join(os.path.dirname(__file__), "..", "data", "predictions.json")
    with open(cache, encoding="utf-8") as f:
        snap = json.load(f)
    teams: set[str] = set()
    for r in snap["rounds"]:
        for m in r["matches"]:
            if not m.get("pending"):
                teams.add(m["home"])
                teams.add(m["away"])
    return sorted(teams)


def main() -> None:
    wc_fd = _wc_team_names()
    if len(wc_fd) < 32:
        raise SystemExit("No hay suficientes equipos en la caché; genera predictions.json primero.")

    df = pd.read_csv(CSV_URL, parse_dates=["date"])

    today = pd.Timestamp(dt.date.today())
    cutoff = today - pd.DateOffset(years=YEARS_WINDOW)
    # Solo partidos jugados (con marcador) dentro de la ventana y hasta hoy.
    df = df[(df.date >= cutoff) & (df.date <= today)].dropna(subset=["home_score", "away_score"])

    # Peso por recencia: exponencial con vida media HALF_LIFE_YEARS.
    age_years = (today - df.date).dt.days / 365.25
    df = df.assign(weight=np.power(0.5, age_years / HALF_LIFE_YEARS))

    # Selecciones con pocos partidos en la ventana → se agrupan en "Other" (estabiliza el ajuste).
    counts = pd.concat([df.home_team, df.away_team]).value_counts()
    frequent = set(counts[counts >= MIN_GAMES].index)
    # Nunca agrupamos a las 48 del Mundial, aunque tuvieran pocos partidos.
    frequent |= set(ALIAS_FD_TO_MARTJ42.get(t, t) for t in wc_fd)

    def bucket(name: str) -> str:
        return name if name in frequent else "Other"

    # Dos filas por partido (una por equipo). home=1 solo si juega en casa (no en campo neutral).
    rows = []
    for r in df.itertuples(index=False):
        home_flag = 0 if bool(r.neutral) else 1
        hg, ag = min(int(r.home_score), GOAL_CAP), min(int(r.away_score), GOAL_CAP)
        rows.append({"goals": hg, "team": bucket(r.home_team), "opp": bucket(r.away_team),
                     "home": home_flag, "weight": float(r.weight)})
        rows.append({"goals": ag, "team": bucket(r.away_team), "opp": bucket(r.home_team),
                     "home": 0, "weight": float(r.weight)})
    data = pd.DataFrame(rows)

    print(f"Partidos en ventana: {len(df)} | filas GLM: {len(data)} | categorias: {data.team.nunique()}")

    model = smf.glm(
        "goals ~ C(team) + C(opp) + home",
        data=data,
        family=sm.families.Poisson(),
        var_weights=data["weight"].to_numpy(),
    ).fit()
    params = model.params

    def attack_effect(martj42_name: str) -> float:
        return float(params.get(f"C(team)[T.{martj42_name}]", 0.0))

    def defense_effect(martj42_name: str) -> float:
        return float(params.get(f"C(opp)[T.{martj42_name}]", 0.0))

    # Resolvemos cada equipo del Mundial a su grafía martj42.
    resolved = {fd: ALIAS_FD_TO_MARTJ42.get(fd, fd) for fd in wc_fd}

    # Centramos los efectos SOBRE el grupo de los 48 (la "selección media del Mundial" → 1.0), igual que
    # hace la tabla a mano y el GLM del torneo, para no romper la calibración del baseline de goles.
    mean_atk = np.mean([attack_effect(m) for m in resolved.values()])
    mean_def = np.mean([defense_effect(m) for m in resolved.values()])

    def mult(effect: float, mean: float) -> float:
        return float(np.clip(math.exp(effect - mean), _MULT_MIN, _MULT_MAX))

    ratings: dict[str, dict] = {}
    for fd, martj42 in resolved.items():
        ratings[normalize_name(fd)] = {
            "attack": round(mult(attack_effect(martj42), mean_atk), 3),
            "defense": round(mult(defense_effect(martj42), mean_def), 3),
            "name": fd,
        }

    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "martj42/international_results",
        "window_years": YEARS_WINDOW,
        "half_life_years": HALF_LIFE_YEARS,
        "teams": ratings,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Sanity check: ranking por "neto" (ataque alto + defensa baja).
    top = sorted(ratings.items(), key=lambda kv: kv[1]["attack"] - kv[1]["defense"], reverse=True)
    print(f"Escrito {os.path.abspath(OUT_PATH)} ({len(ratings)} selecciones)")
    print("Top 8 (ataque - defensa):")
    for norm, r in top[:8]:
        print(f"  {r['name']:18} atk={r['attack']:.2f} def={r['defense']:.2f}")
    print("Bottom 4:")
    for norm, r in top[-4:]:
        print(f"  {r['name']:18} atk={r['attack']:.2f} def={r['defense']:.2f}")


if __name__ == "__main__":
    main()
