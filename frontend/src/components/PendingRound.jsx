// Panel para una eliminatoria cuyos cruces aún no se conocen: en vez de N tarjetas vacías, un único
// aviso con el número de partidos y el rango de fechas. Se rellenará solo cuando haya equipos.

import { formatDay } from "../lib/format.js";

export default function PendingRound({ round }) {
  const dates = round.matches
    .map((m) => m.utcDate)
    .filter(Boolean)
    .sort();
  const range =
    dates.length > 0 ? `${formatDay(dates[0])} – ${formatDay(dates[dates.length - 1])}` : null;

  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white/60 px-6 py-12 text-center">
      <div className="mb-3 text-4xl">🔒</div>
      <h3 className="text-lg font-bold text-slate-700">{round.stage_label} · por definir</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
        {round.matches.length} {round.matches.length === 1 ? "partido" : "partidos"}
        {range && ` · ${range}`}. Los emparejamientos se conocerán cuando terminen las rondas
        anteriores. Esta sección <strong className="text-slate-700">se rellenará automáticamente</strong>{" "}
        con las predicciones en cuanto haya equipos.
      </p>
    </div>
  );
}
