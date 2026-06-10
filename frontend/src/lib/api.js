// Cliente del frontend: SOLO lee /predictions del backend (nunca toca la API de fútbol).
// El backend sirve una caché que se regenera una vez al día, así que esto es barato e ilimitado.

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function fetchPredictions() {
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
