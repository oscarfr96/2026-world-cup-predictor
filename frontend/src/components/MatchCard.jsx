// Tarjeta de un partido: fecha, marcador (goles esperados por equipo, o reales si ya se jugó),
// favorito, barras 1X2 y marcadores más probables. Si ya se jugó, flag de acierto (✓) o fallo (✗).

import { formatDateTime } from "../lib/format.js";

function Bar({ label, value, color, highlight }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-24 shrink-0 truncate text-slate-500">{label}</span>
      <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span
        className={`w-9 shrink-0 text-right text-xs font-semibold tabular-nums ${
          highlight ? "text-slate-800" : "text-slate-400"
        }`}
      >
        {pct}%
      </span>
    </div>
  );
}

// Una fila del "marcador": nombre del equipo (ganador en verde) + su número (goles esperados o reales).
function TeamRow({ name, value, isWinner }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className={`font-bold ${isWinner ? "text-emerald-600" : "text-slate-900"}`}>{name}</span>
      <span className="shrink-0 text-base font-bold tabular-nums text-slate-700">{value}</span>
    </div>
  );
}

export default function MatchCard({ match }) {
  const {
    home,
    away,
    expected_goals,
    outcome,
    winner,
    favorite,
    likely_score,
    most_likely_scores,
    utcDate,
  } = match;

  // Goles reales si ya se jugó (de "3-0"); si no, los goles esperados (λ) del modelo.
  const [realHome, realAway] = match.played ? match.real_score.split("-") : [null, null];
  const homeValue = match.played ? realHome : expected_goals.home;
  const awayValue = match.played ? realAway : expected_goals.away;

  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      {/* Cabecera: fecha + (si jugado) acierto/fallo */}
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-slate-400">{formatDateTime(utcDate)}</span>
        {match.played && (
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
              match.correct ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-600"
            }`}
          >
            {match.correct ? "✓ Acerté" : "✗ Fallé"}
          </span>
        )}
      </div>

      {/* Marcador: cada equipo con su número (ganador en verde) */}
      <div className="space-y-1">
        <TeamRow name={home} value={homeValue} isWinner={winner === "home"} />
        <TeamRow name={away} value={awayValue} isWinner={winner === "away"} />
      </div>

      {/* Qué significan esos números */}
      <p
        className="mt-1 text-[11px] text-slate-400"
        title="Media de goles que el modelo espera de cada equipo. No es el marcador predicho."
      >
        {match.played ? "Resultado final" : "Goles esperados por equipo (media del modelo)"}
      </p>

      {/* Favorito + marcador probable */}
      <div className="mt-3 flex flex-wrap items-center gap-x-1.5 text-sm">
        <span className="text-amber-500">⭐</span>
        <span className="font-semibold text-slate-700">{favorite}</span>
        <span className="text-slate-400">· probable</span>
        <span className="font-semibold text-slate-700">{likely_score.score}</span>
      </div>

      {/* Barras 1X2 */}
      <div className="mt-3 space-y-1.5">
        <Bar label={home} value={outcome.home} color="bg-sky-500" highlight={winner === "home"} />
        <Bar label="Empate" value={outcome.draw} color="bg-amber-400" highlight={winner === "draw"} />
        <Bar label={away} value={outcome.away} color="bg-rose-500" highlight={winner === "away"} />
      </div>

      {/* Marcadores más probables */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {most_likely_scores.map((s) => (
          <span key={s.score} className="rounded-md bg-slate-50 px-2 py-0.5 text-xs text-slate-500">
            {s.score} <span className="font-semibold text-slate-400">{Math.round(s.prob * 100)}%</span>
          </span>
        ))}
      </div>
    </div>
  );
}
