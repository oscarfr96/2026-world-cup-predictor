"""PRIOR: fuerza de cada selección → multiplicadores de ataque/defensa.

El prior sale de un modelo PRE-ENTRENADO sobre partidos internacionales recientes (ver
`scripts/build_prior.py`, dataset martj42): un GLM de Poisson aprende el ataque/defensa de cada
selección con clasificación, Nations League, amistosos, etc. Su salida vive en
`international_ratings.json` y se carga aquí. Así el modelo llega al Mundial "caliente" (sin cold
start) y con un prior OBJETIVO, no a ojo.

  - attack  > 1  → la selección marca por encima de la media del torneo.
  - defense > 1  → la selección encaja por encima de la media (defensa DÉBIL). Como es el RIVAL en
                   la fórmula, una defense alta del rival sube los goles esperados del otro equipo.

Como red de seguridad, si falta el fichero o una selección no está en él, se usa una tabla manual de
respaldo (`_STRENGTH`, ≈ tiers del ranking FIFA). En el torneo, estos números se MEZCLAN con lo
aprendido de los goles reales del Mundial vía shrinkage (blend.py).
"""

from __future__ import annotations

import json
import os
import unicodedata


def normalize_name(name: str) -> str:
    """Minúsculas + sin acentos, para cruzar nombres de equipos entre fuentes."""
    nfkd = unicodedata.normalize("NFKD", name or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _load_prior_ratings() -> dict[str, dict]:
    """Carga el prior pre-entrenado (international_ratings.json). {} si no existe (usa el respaldo)."""
    path = os.path.join(os.path.dirname(__file__), "international_ratings.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("teams", {})
    except (OSError, json.JSONDecodeError):
        return {}


# Prior objetivo por selección (clave = nombre normalizado). Vacío → se cae a la tabla de respaldo.
_PRIOR_RATINGS = _load_prior_ratings()


# Selecciones anfitrionas del Mundial 2026: son las únicas que juegan de local de verdad (en su país),
# así que son las únicas a las que el modelo aplica ventaja de campo. El resto, sede neutral.
HOST_NATIONS = {"united states", "canada", "mexico", "usa"}


def is_host_nation(team_name: str) -> bool:
    """True si la selección es anfitriona (EE. UU., Canadá o México)."""
    return normalize_name(team_name) in HOST_NATIONS


# Tabla de RESPALDO (≈ tiers del ranking FIFA). Solo se usa si falta el prior pre-entrenado o una
# selección no aparece en él. Claves = nombre normalizado de football-data.org, con algunos alias.
_STRENGTH: dict[str, float] = {
    # --- Favoritas ---
    "argentina": 0.97, "france": 0.96, "brazil": 0.94, "spain": 0.95, "england": 0.93,
    "portugal": 0.92, "netherlands": 0.90, "belgium": 0.88, "germany": 0.87,
    # --- Contenders ---
    "uruguay": 0.85, "croatia": 0.84, "colombia": 0.84, "morocco": 0.83, "senegal": 0.80,
    "switzerland": 0.80, "japan": 0.79, "norway": 0.79, "united states": 0.78, "mexico": 0.78,
    # --- Medio ---
    "austria": 0.77, "turkey": 0.77, "ecuador": 0.76, "south korea": 0.76, "czechia": 0.75,
    "sweden": 0.74, "iran": 0.74, "egypt": 0.74, "canada": 0.74, "algeria": 0.73,
    "ivory coast": 0.73, "scotland": 0.72, "paraguay": 0.71, "australia": 0.71,
    # --- Medio-bajo ---
    "tunisia": 0.70, "ghana": 0.70, "bosnia-herzegovina": 0.70, "south africa": 0.66,
    "congo dr": 0.66, "uzbekistan": 0.66, "panama": 0.64, "saudi arabia": 0.63,
    "qatar": 0.62, "cape verde islands": 0.62, "iraq": 0.62, "jordan": 0.60,
    # --- Outsiders ---
    "haiti": 0.56, "new zealand": 0.56, "curacao": 0.55,
    # --- Alias por si cambia la grafía en otra fuente/fase ---
    "usa": 0.78, "korea republic": 0.76, "cote d'ivoire": 0.73, "czech republic": 0.75,
    "dr congo": 0.66, "cape verde": 0.62,
}

DEFAULT_STRENGTH = 0.55  # selección desconocida → ligeramente por debajo de la media


def strength_scalar(team_name: str) -> float:
    return _STRENGTH.get(normalize_name(team_name), DEFAULT_STRENGTH)


# Selección "media" del torneo: su fuerza mapea a multiplicadores 1.0 (ataque y defensa neutros).
REF_STRENGTH = 0.70
_SPREAD = 1.4  # cuánto se separan los multiplicadores de 1.0 según la distancia a la media


def _fallback_attack_defense(team_name: str) -> dict[str, float]:
    """Respaldo: deriva los multiplicadores de la tabla manual (≈ tiers FIFA) si no hay prior."""
    s = strength_scalar(team_name)
    delta = _SPREAD * (s - REF_STRENGTH)
    attack = max(0.5, min(1.5, 1.0 + delta))
    defense = max(0.5, min(1.5, 1.0 - delta))
    return {"attack": round(attack, 3), "defense": round(defense, 3), "strength": s}


def attack_defense(team_name: str) -> dict[str, float]:
    """Multiplicadores de ataque/defensa (prior) de una selección.

    Primero usa el prior pre-entrenado con partidos internacionales (international_ratings.json);
    si la selección no está ahí o falta el fichero, cae a la tabla de respaldo (≈ tiers FIFA).
    """
    rec = _PRIOR_RATINGS.get(normalize_name(team_name))
    if rec:
        return {"attack": rec["attack"], "defense": rec["defense"], "source": "international"}
    return _fallback_attack_defense(team_name)
