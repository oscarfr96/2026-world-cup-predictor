// Tarjeta de un partido: fecha, favorito, goles esperados (λ), barras 1X2, marcadores probables y,
// si ya se jugó, el resultado real con el flag de acierto (✓) o fallo (✗).

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

  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      {/* Cabecera: fecha + estado/resultado */}
      <div className="mb-3 flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-slate-400">{formatDateTime(utcDate)}</span>
        {match.played ? (
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
              match.correct ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-600"
            }`}
          >
            {match.correct ? "✓ Acerté" : "✗ Fallé"} · {match.real_score}
          </span>
        ) : (
          <span
            className="rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-medium text-sky-600"
            title="Media de goles que el modelo espera de cada equipo (en el orden de los nombres). No es el marcador predicho."
          >
            Goles esp. {expected_goals.home}–{expected_goals.away}
          </span>
        )}
      </div>

      {/* Equipos: nombre en negro, ganador previsto en verde */}
      <div className="mb-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-[15px] font-bold">
        <span className={winner === "home" ? "text-emerald-600" : "text-slate-900"}>{home}</span>
        <span className="text-xs font-normal text-slate-300">vs</span>
        <span className={winner === "away" ? "text-emerald-600" : "text-slate-900"}>{away}</span>
      </div>

      {/* Favorito + marcador probable */}
      <div className="mb-3 flex flex-wrap items-center gap-x-1.5 text-sm">
        <span className="text-amber-500">⭐</span>
        <span className="font-semibold text-slate-700">{favorite}</span>
        <span className="text-slate-400">· probable</span>
        <span className="font-semibold text-slate-700">{likely_score.score}</span>
      </div>

      {/* Barras 1X2 */}
      <div className="space-y-1.5">
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
