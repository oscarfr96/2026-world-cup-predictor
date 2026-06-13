// Cliente del frontend: lee las predicciones (nunca toca la API de fútbol).
//
// Fuente principal: /api/predictions (función de Vercel que lee el snapshot persistido en Blob). Es
// durable: no depende de que el backend de Render esté despierto ni de su disco efímero (que al
// reciclarse vuelve a la semilla vieja → "0 partidos jugados"). Fallback: el /predictions del backend
// (puede estar obsoleto, pero es mejor que nada y cubre el arranque antes de conectar el Blob, y el
// desarrollo local donde /api/* no se sirve con Vite).

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function fetchPredictions() {
  // 1) Blob vía función de Vercel.
  try {
    const res = await fetch("/api/predictions");
    if (res.ok) return res.json();
    if (res.status !== 404) {
      throw new Error(`Error ${res.status} al cargar las predicciones.`);
    }
    // 404 → Blob aún no configurado/poblado: caemos al backend.
  } catch {
    // Red/parseo → probamos el backend.
  }

  // 2) Fallback: backend en Render.
  const res = await fetch(`${API_BASE}/predictions`);
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Todavía no hay predicciones generadas. Vuelve en un rato.");
    }
    throw new Error(`Error ${res.status} al cargar las predicciones.`);
  }
  return res.json();
}

// Track record honesto (predicciones congeladas vs resultado). Lo sirve una función de Vercel que
// lee el registro persistido en Vercel Blob. Devuelve null si todavía no se ha generado (404).
export async function fetchTrackRecord() {
  const res = await fetch("/api/track-record");
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Error ${res.status} al cargar el historial.`);
  return res.json();
}
