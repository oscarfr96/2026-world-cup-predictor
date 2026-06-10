"""Tests del pipeline con partidos simulados (sin red): fase 1, acierto/fallo y fase 2."""

from app.pipeline import build_snapshot


def _match(home, away, stage, matchday, status="SCHEDULED", hg=None, ag=None, date="2026-06-11T18:00:00Z"):
    return {
        "utcDate": date, "status": status, "home": home, "away": away,
        "matchday": matchday, "stage": stage, "home_goals": hg, "away_goals": ag,
    }


def test_fase_sin_resultados_es_pretrained():
    matches = [
        _match("Spain", "Croatia", "GROUP_STAGE", 1),
        _match("Brazil", "Curacao", "GROUP_STAGE", 1),
    ]
    snap = build_snapshot(matches)
    # Sin partidos del Mundial aún, manda el prior pre-entrenado (no es cold start).
    assert snap["phase"] == "pretrained"
    assert snap["matches_played"] == 0
    assert snap["accuracy"]["evaluated"] == 0
    # Cada partido trae favorito, goles esperados y marcadores.
    p = snap["rounds"][0]["matches"][0]
    assert "favorite" in p and "expected_goals" in p and p["played"] is False


def test_partido_jugado_marca_acierto():
    # Brasil gana a Curacao 3-0: el modelo (que hace favorito a Brasil) debe acertar.
    matches = [_match("Brazil", "Curacao", "GROUP_STAGE", 1, status="FINISHED", hg=3, ag=0)]
    snap = build_snapshot(matches)
    p = snap["rounds"][0]["matches"][0]
    assert p["played"] is True
    assert p["real_score"] == "3-0"
    assert p["correct"] is True
    assert snap["accuracy"]["evaluated"] == 1


def test_rondas_ordenadas_grupos_antes_que_final():
    matches = [
        _match("A", "B", "FINAL", None, date="2026-07-19T18:00:00Z"),
        _match("C", "D", "GROUP_STAGE", 1, date="2026-06-11T18:00:00Z"),
    ]
    snap = build_snapshot(matches)
    assert snap["rounds"][0]["stage"] == "GROUP_STAGE"
    assert snap["rounds"][-1]["stage"] == "FINAL"
