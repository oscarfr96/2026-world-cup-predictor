// Página /historial: el track record honesto. Para cada partido muestra la predicción CONGELADA
// (la que el modelo dio antes del saque) y, si ya se jugó, el resultado real y si se acertó.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchTrackRecord } from "../lib/api.js";
import { formatDateTime, roundLabel } from "../lib/format.js";
import Loading from "../components/Loading.jsx";

function pct(v) {
  return `${Math.round(v * 100)}%`;
}

function TrackMatch({ m }) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
      <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
        <span>{formatDateTime(m.utcDate)}</span>
        {m.played ? (
          <span
            className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
              m.correct ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-600"
            }`}
          >
            {m.correct ? "✓ Acierto" : "✗ Fallo"} · {m.real_score}
          </span>
        ) : (
          <span className="text-[11px] text-slate-400">Pendiente</span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-2 text-sm font-bold">
        <span className={m.pred_winner === "home" ? "text-sky-600" : "text-slate-700"}>{m.home}</span>
        <span className="text-xs font-normal text-slate-300">vs</span>
        <span className={m.pred_winner === "away" ? "text-rose-600" : "text-slate-700"}>{m.away}</span>
      </div>

      <div className="mt-1 text-xs text-slate-500">
        Predije: <span className="font-semibold text-slate-700">{m.pred_favorite}</span>{" "}
        <span className="text-slate-400">
          ({pct(m.pred_outcome.home)} / {pct(m.pred_outcome.draw)} / {pct(m.pred_outcome.away)})
        </span>
      </div>

      {m.locked_before_kickoff === false && (
        <div className="mt-1 text-[11px] italic text-amber-600">
          registrado tras el inicio (no cuenta como predicción a ciegas)
        </div>
      )}
    </div>
  );
}

export default function TrackRecord() {
  const [data, setData] = useState(undefined); // undefined = cargando, null = aún no hay
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTrackRecord()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="px-4 py-20 text-center text-rose-600">{error}</p>;
  if (data === undefined) return <Loading />;

  if (data === null) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <div className="mb-3 text-4xl">📒</div>
        <h1 className="text-lg font-bold text-slate-700">Aún no hay historial</h1>
        <p className="mt-2 text-sm text-slate-500">
          El registro de aciertos se genera automáticamente cada día. Vuelve cuando empiece a rodar el
          balón.
        </p>
        <Link to="/" className="mt-4 inline-block text-sm font-semibold text-sky-600 hover:underline">
          ← Volver a las predicciones
        </Link>
      </div>
    );
  }

  const acc = data.accuracy;
  const roundsConPartidos = data.rounds.filter((r) => r.matches.length > 0);

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <section className="mb-6 rounded-3xl bg-white/70 p-6 ring-1 ring-slate-100 sm:p-8">
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-800 sm:text-3xl">
          Mi{" "}
          <span className="bg-gradient-to-r from-sky-500 via-violet-500 to-rose-500 bg-clip-text text-transparent">
            track record
          </span>
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Cada predicción se <strong className="text-slate-600">congela antes del partido</strong> y se
          compara con el resultado. Sin retoques a posteriori.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {acc?.pct != null ? (
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-200">
              🎯 Acierto {acc.pct}% ({acc.correct}/{acc.evaluated})
            </span>
          ) : (
            <span className="rounded-full bg-white/80 px-3 py-1 text-sm font-medium text-slate-500 ring-1 ring-slate-200">
              Aún no hay partidos jugados para evaluar
            </span>
          )}
        </div>
      </section>

      <div className="space-y-8">
        {roundsConPartidos.map((r) => (
          <section key={r.key}>
            <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">
              {roundLabel(r)}
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {r.matches.map((m, i) => (
                <TrackMatch key={`${m.id}-${i}`} m={m} />
              ))}
            </div>
          </section>
        ))}
      </div>

      <div className="mt-8 text-center">
        <Link to="/" className="text-sm font-semibold text-sky-600 hover:underline">
          ← Volver a las predicciones
        </Link>
      </div>
    </div>
  );
}
