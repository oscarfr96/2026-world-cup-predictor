// Actualiza el "track record" honesto de predicciones y lo persiste en Vercel Blob.
//
// Idea: cada día (lo lanza el GitHub Action tras el recompute) leemos las predicciones actuales del
// backend y CONGELAMOS la predicción de cada partido ANTES de que se juegue. Una vez el partido ha
// empezado, su predicción ya no se toca nunca más (así no hay "sesgo de retrovisor": el modelo no
// reescribe lo que dijo). Para los partidos ya jugados comparamos la predicción congelada con el
// resultado real → ✓/✗ y % de acierto honesto.
//
// Persistencia: Vercel Blob (fichero estable `track-record.json`). Si no hay BLOB_READ_WRITE_TOKEN,
// cae a un fichero local (para pruebas).
//
// Env: API_URL (base del backend), BLOB_READ_WRITE_TOKEN (opcional en local).

import fs from "node:fs";

const API_URL = process.env.API_URL;
const TOKEN = process.env.BLOB_READ_WRITE_TOKEN || "";
const PATHNAME = "track-record.json";
const LOCAL = "backend/data/track-record.local.json"; // solo para pruebas sin token

if (!API_URL) {
  console.error("Falta API_URL");
  process.exit(1);
}

// Estados que indican que el partido YA empezó (y por tanto su predicción queda congelada).
const STARTED = new Set(["IN_PLAY", "PAUSED", "FINISHED", "SUSPENDED", "AWARDED"]);

function lockedFieldsFrom(p, phase, beforeKickoff, lockedAt) {
  return {
    locked_at: lockedAt,
    phase_at_lock: phase,
    locked_before_kickoff: beforeKickoff,
    pred_winner: p.winner,
    pred_favorite: p.favorite,
    pred_outcome: p.outcome,
    pred_expected_goals: p.expected_goals,
    pred_likely_score: p.likely_score,
  };
}

function keepLockedFrom(prior) {
  return {
    locked_at: prior.locked_at,
    phase_at_lock: prior.phase_at_lock,
    locked_before_kickoff: prior.locked_before_kickoff,
    pred_winner: prior.pred_winner,
    pred_favorite: prior.pred_favorite,
    pred_outcome: prior.pred_outcome,
    pred_expected_goals: prior.pred_expected_goals,
    pred_likely_score: prior.pred_likely_score,
  };
}

async function load() {
  if (TOKEN) {
    const { list } = await import("@vercel/blob");
    const { blobs } = await list({ prefix: PATHNAME, token: TOKEN });
    const hit = blobs.find((b) => b.pathname === PATHNAME);
    if (!hit) return null;
    // Store privado → la URL requiere autenticación con el token.
    const res = await fetch(hit.url, {
      cache: "no-store",
      headers: { authorization: `Bearer ${TOKEN}` },
    });
    return res.ok ? await res.json() : null;
  }
  try {
    return JSON.parse(fs.readFileSync(LOCAL, "utf8"));
  } catch {
    return null;
  }
}

async function save(data) {
  const body = JSON.stringify(data, null, 2);
  if (TOKEN) {
    const { put } = await import("@vercel/blob");
    const r = await put(PATHNAME, body, {
      access: "private",
      addRandomSuffix: false,
      allowOverwrite: true,
      contentType: "application/json",
      token: TOKEN,
    });
    console.log("Track record guardado en Blob:", r.url);
  } else {
    fs.writeFileSync(LOCAL, body);
    console.log("Track record guardado en local:", LOCAL);
  }
}

async function main() {
  const res = await fetch(`${API_URL}/predictions`, { headers: { accept: "application/json" } });
  if (!res.ok) {
    console.error(`Backend /predictions devolvió HTTP ${res.status}`);
    process.exit(1);
  }
  const snap = await res.json();

  const prior = (await load()) || { rounds: [] };
  const priorById = {};
  for (const r of prior.rounds || []) for (const m of r.matches || []) priorById[m.id] = m;

  const now = new Date().toISOString();
  const rounds = [];
  let correct = 0;
  let evaluated = 0;

  for (const r of snap.rounds) {
    if (r.pending) continue; // eliminatoria sin equipos → nada que registrar todavía
    const matches = [];
    for (const p of r.matches) {
      if (p.pending) continue;
      const prev = priorById[p.id];
      const started = STARTED.has(p.status);

      let rec;
      if (!started) {
        // Aún no ha empezado → (re)congelamos la última predicción antes del saque.
        rec = lockedFieldsFrom(p, snap.phase, true, now);
      } else if (prev && prev.pred_winner) {
        // Ya empezó y teníamos predicción previa → la mantenemos intacta (sin retrovisor).
        rec = keepLockedFrom(prev);
      } else {
        // Empezó y nunca lo vimos antes → lo registramos, marcando que NO fue pre-saque (transparencia).
        rec = lockedFieldsFrom(p, snap.phase, false, (prev && prev.locked_at) || now);
      }

      rec.id = p.id;
      rec.home = p.home;
      rec.away = p.away;
      rec.utcDate = p.utcDate;
      rec.status = p.status;
      rec.played = !!p.played;

      if (p.played) {
        rec.real_score = p.real_score;
        rec.real_result = p.real_result;
        rec.correct = rec.pred_winner === p.real_result;
        evaluated += 1;
        if (rec.correct) correct += 1;
      }
      matches.push(rec);
    }
    rounds.push({
      stage: r.stage,
      stage_label: r.stage_label,
      matchday: r.matchday,
      key: r.key,
      matches,
    });
  }

  const out = {
    generated_at: now,
    phase: snap.phase,
    accuracy: {
      correct,
      evaluated,
      pct: evaluated ? Math.round((1000 * correct) / evaluated) / 10 : null,
    },
    rounds,
  };

  await save(out);
  console.log(`OK · ${rounds.length} rondas · acierto ${out.accuracy.pct ?? "—"}% (${correct}/${evaluated})`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
