// Página "secreta" /today (no enlazada en la navegación): los partidos de HOY con su predicción,
// en formato compacto pensado para caber en una captura de pantalla para los vídeos.

import { useEffect, useState } from "react";
import { fetchPredictions } from "../lib/api.js";
import { formatTime, isToday } from "../lib/format.js";
import Loading from "../components/Loading.jsx";

const OUTCOME = {
  home: { color: "bg-sky-500", text: "text-sky-600" },
  draw: { color: "bg-amber-400", text: "text-amber-600" },
  away: { color: "bg-rose-500", text: "text-rose-600" },
};

function MiniBar({ value, color }) {
  return (
    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  );
}

function TodayMatch({ m }) {
  const pct = (v) => `${Math.round(v * 100)}%`;
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400">{formatTime(m.utcDate)}</span>
        {m.played ? (
          <span
            className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
              m.correct ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-600"
            }`}
          >
            {m.real_score} {m.correct ? "✓" : "✗"}
          </span>
        ) : (
          <span className="text-[11px] text-slate-400">
            λ {m.expected_goals.home}–{m.expected_goals.away}
          </span>
        )}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <span className={`font-bold ${m.winner === "home" ? "text-emerald-600" : "text-slate-900"}`}>
          {m.home}
        </span>
        <span className="text-xs text-slate-300">vs</span>
        <span className={`text-right font-bold ${m.winner === "away" ? "text-emerald-600" : "text-slate-900"}`}>
          {m.away}
        </span>
      </div>

      <div className="mt-1 text-center text-xs text-slate-500">
        <span className="text-amber-500">⭐</span> {m.favorite} · {m.likely_score.score}
      </div>

      {/* Barra 1X2 con porcentajes */}
      <div className="mt-2 flex items-center gap-2">
        <MiniBar value={m.outcome.home} color={OUTCOME.home.color} />
        <MiniBar value={m.outcome.draw} color={OUTCOME.draw.color} />
        <MiniBar value={m.outcome.away} color={OUTCOME.away.color} />
      </div>
      <div className="mt-1 flex justify-between text-[11px] font-semibold tabular-nums">
        <span className={OUTCOME.home.text}>{pct(m.outcome.home)}</span>
        <span className={OUTCOME.draw.text}>{pct(m.outcome.draw)}</span>
        <span className={OUTCOME.away.text}>{pct(m.outcome.away)}</span>
      </div>
    </div>
  );
}

export default function Today() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPredictions().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="px-4 py-20 text-center text-rose-600">{error}</p>;
  if (!data) return <Loading />;

  const today = data.rounds
    .flatMap((r) => r.matches)
    .filter((m) => !m.pending && isToday(m.utcDate))
    .sort((a, b) => (a.utcDate || "").localeCompare(b.utcDate || ""));

  const fecha = new Date().toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <div className="mx-auto max-w-md px-4 py-6">
      <div className="rounded-3xl bg-white/70 p-5 ring-1 ring-slate-100">
        {/* Cabecera para la captura */}
        <div className="mb-4 text-center">
          <div className="text-3xl">⚽</div>
          <h1 className="mt-1 text-xl font-extrabold text-slate-800">Partidos de hoy</h1>
          <p className="text-sm capitalize text-slate-500">{fecha}</p>
        </div>

        {today.length === 0 ? (
          <p className="py-10 text-center text-slate-500">
            Hoy no hay partidos con equipos definidos. ¡Vuelve otro día! 🗓️
          </p>
        ) : (
          <div className="space-y-3">
            {today.map((m, i) => (
              <TodayMatch key={`${m.home}-${m.away}-${i}`} m={m} />
            ))}
          </div>
        )}

        {/* Marca de agua para los vídeos */}
        <p className="mt-5 text-center text-[11px] font-medium text-slate-400">
          oscar-wc-predictor.vercel.app · predicción del modelo
        </p>
      </div>
    </div>
  );
}
