// Utilidades de formato y constantes compartidas por la UI.

export const REPO_URL = "https://github.com/oscarfr96/2026-world-cup-predictor";

// "11 jun, 21:00" — fecha + hora local del visitante.
export function formatDateTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("es-ES", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// "11 jun" — solo el día, para rangos de fechas.
export function formatDay(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("es-ES", { day: "numeric", month: "short" });
}

// "21:00" — solo la hora local.
export function formatTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
}

// ¿Cae este ISO en el día de HOY (zona horaria local del visitante)?
export function isToday(iso) {
  if (!iso) return false;
  const d = new Date(iso);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

// Etiqueta corta de una ronda para el selector: "Grupos · J1" o "Cuartos".
export function roundLabel(round) {
  if (round.stage === "GROUP_STAGE" && round.matchday) return `Grupos · J${round.matchday}`;
  return round.stage_label;
}

// Texto del momento del modelo.
export function phaseLabel(phase) {
  return phase === "trained"
    ? "Ajustado con resultados del Mundial"
    : "Pre-entrenado con partidos internacionales";
}
