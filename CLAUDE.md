# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Open-source 2026 World Cup match predictor. The README (Spanish) is the canonical, detailed reference for the model and architecture — read it for the full story. Code comments are in Spanish; keep that convention when editing.

## Commands

Backend (run from `backend/`, with a venv and `pip install -r requirements.txt`):

```bash
uvicorn app.main:app --reload            # dev server on :8000
python -m scripts.recompute_local        # regenerate data/predictions.json locally (needs FOOTBALL_DATA_ORG_KEY in backend/.env)
python -m scripts.build_prior            # rebuild app/model/international_ratings.json from international results (offline artifact)
pytest                                   # all tests
pytest tests/test_pipeline.py::<name>    # single test
```

Frontend (run from `frontend/`):

```bash
npm install
npm run dev        # Vite dev server on :5173 (expects backend at VITE_API_BASE, default http://localhost:8000)
npm run build      # production build
```

Track record updater (run from repo root, used by CI):

```bash
node scripts/update-track-record.mjs     # needs API_URL; BLOB_READ_WRITE_TOKEN optional (falls back to local file)
```

## The central design constraint: COMPUTE vs READ

The only external data source, `football-data.org`, is free but rate-limited (10 req/min). The entire architecture exists to call it **at most once per day** while serving unlimited visitors:

- **Expensive path (once/day):** `POST /admin/recompute` fetches fresh data, runs the model, and freezes the result into a JSON cache (`backend/data/predictions.json`). It's protected by a token (`X-Recompute-Token` header) **and** a date guard — even if called repeatedly, only the first call of the day hits the external API (`force=true` bypasses the guard and spends an API call). Triggered by GitHub Actions (`.github/workflows/daily-recompute.yml`, 09:00 UTC), **not** a Render cron (Render's free plan dropped cron).
- **Cheap path (every visit):** `GET /predictions` only reads and returns the cache, never touching the external API. Rate-limited to 60/min per IP via slowapi (real client IP from `X-Forwarded-For`, since uvicorn runs behind Render's proxy with `--proxy-headers`).

When changing data flow, preserve this boundary: `pipeline.py`/`football_data.py` are the **only** code allowed to call the external API, and only `recompute` invokes them. `main.py` knows nothing about the model — it orchestrates HTTP and persistence.

## The model: a two-phase pipeline

Same pipeline throughout — **strength → expected goals (λ) → score matrix → 1X2 + favorite**. Only the *source of strength* changes between phases.

- **Phase 1 (prior, pre-trained):** `scripts/build_prior.py` pre-trains a Poisson GLM on recent international matches (martj42 open dataset) and writes `app/model/international_ratings.json` (a committed, versioned artifact — not generated in production). `strength.py` loads it as the prior; if a team or the file is missing, it falls back to the hand-built `_STRENGTH` table (≈ FIFA tiers).
- **Phase 2 (trained on the tournament):** once ≥8 World Cup matches are played, `train.py` fits a Poisson GLM (`goals ~ C(team) + C(opp) + home`) on real tournament goals. Coefficients become attack/defense multipliers centered on 1.0 (same scale as the prior).
- **Blend (shrinkage):** `blend.py` combines prior and learned strength with `weight = n / (n + k)` (`k = PSEUDO_COUNT = 3`). Few games → prior dominates; many games → tournament data dominates. This prevents a single blowout from rewriting a team's rating.

Key model files:
- `model/strength.py` — prior lookup + name normalization + host-nation logic. Home advantage applies **only** to host nations (USA, Canada, Mexico — the only teams playing in their own country; rest is neutral ground).
- `model/poisson.py` — λ from attack×defense, Poisson score matrix, Dixon-Coles low-score correction, 1X2/favorite.
- `model/blend.py` / `model/train.py` — shrinkage and Phase-2 GLM.
- `pipeline.py` — orchestrates: fetch → train → per-match predict → compare to real result → snapshot.

Attack/defense convention throughout: `attack > 1` = scores above tournament average; `defense > 1` = a **weak** defense (concedes a lot). Since defense is the *opponent's* in the λ formula, a high opponent defense raises your expected goals.

## Track record (honest, no hindsight)

`scripts/update-track-record.mjs` (run daily by CI after recompute) freezes each match's prediction **before kickoff** and never rewrites it once the match has started (`STARTED` statuses). Persisted to Vercel Blob as `track-record.json`. The frontend reads it via the Vercel serverless function `frontend/api/track-record.js` (`GET /api/track-record`), which returns 404 until the Blob store is connected.

## Why predictions are also served from Blob (Render free is ephemeral)

Render's free disk is **ephemeral** and the service **sleeps on inactivity**: every recompute writes `predictions.json` to that disk, but on spin-down it reverts to the **committed seed** (`backend/data/predictions.json`) — so `GET /predictions` from Render goes stale (e.g. "0 partidos jugados"). To keep the public site durable, the daily job also publishes the fresh snapshot to Vercel Blob as `predictions.json` (`scripts/publish-predictions.mjs`), served via `frontend/api/predictions.js` (`GET /api/predictions`). The frontend (`lib/api.js`) reads `/api/predictions` first and **falls back** to the Render backend (`VITE_API_BASE/predictions`) on 404/error — the fallback covers local dev (Vite doesn't serve `/api/*`) and the window before the Blob store is connected. Render is effectively the compute worker; Blob is the durable read path.

## Deployment topology

- **Backend** → Render (`render.yaml`). Secrets (`FOOTBALL_DATA_ORG_KEY`, `RECOMPUTE_TOKEN`, `ALLOWED_ORIGIN`) are `sync:false` — set them in the Render dashboard, never in the repo.
- **Frontend** → Vercel (React + Vite + Tailwind, React Router with SPA rewrite in `vercel.json`). Reads `/api/predictions` (Blob, with fallback to `VITE_API_BASE/predictions`) and `/api/track-record` — both Vercel serverless functions backed by Vercel Blob. Routes (`App.jsx`): `/` (Predictions), `/historial` (TrackRecord), `/modelo` (ModelInfo), and `/today` — a **hidden** page (not in the nav, used for generating videos).
- **Daily job** → GitHub Actions. Secrets: `API_URL`, `RECOMPUTE_TOKEN` (must match Render's), `BLOB_READ_WRITE_TOKEN`.

All secrets live only in environment variables; the backend degrades gracefully if they're missing (`/health` always responds, `/predictions` serves whatever cache exists).
