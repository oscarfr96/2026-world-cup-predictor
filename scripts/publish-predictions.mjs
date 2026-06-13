// Publica el snapshot de predicciones del día en Vercel Blob (fichero estable `predictions.json`).
//
// Por qué: el disco del plan free de Render es efímero y el servicio se duerme; cuando se recicla,
// /predictions vuelve a la semilla commiteada (datos viejos). Para que la web no dependa del uptime
// de Render, tras el recompute leemos /predictions UNA vez (con la instancia aún despierta) y
// congelamos ese snapshot en Blob. La web lo sirve desde ahí (frontend/api/predictions.js), durable.
//
// Lo lanza el GitHub Action tras el recompute, igual que update-track-record.mjs.
//
// Env: API_URL (base del backend), BLOB_READ_WRITE_TOKEN (obligatorio aquí; en local cae a fichero).

import fs from "node:fs";

const API_URL = process.env.API_URL;
const TOKEN = process.env.BLOB_READ_WRITE_TOKEN || "";
const PATHNAME = "predictions.json";
const LOCAL = "backend/data/predictions.blob.local.json"; // solo para pruebas sin token

if (!API_URL) {
  console.error("Falta API_URL");
  process.exit(1);
}

async function main() {
  const res = await fetch(`${API_URL}/predictions`, { headers: { accept: "application/json" } });
  if (!res.ok) {
    console.error(`Backend /predictions devolvió HTTP ${res.status}`);
    process.exit(1);
  }
  const snap = await res.json();
  const body = JSON.stringify(snap, null, 2);

  if (TOKEN) {
    const { put } = await import("@vercel/blob");
    const r = await put(PATHNAME, body, {
      access: "private",
      addRandomSuffix: false,
      allowOverwrite: true,
      contentType: "application/json",
      token: TOKEN,
    });
    console.log("Predicciones guardadas en Blob:", r.url);
  } else {
    fs.writeFileSync(LOCAL, body);
    console.log("Predicciones guardadas en local:", LOCAL);
  }

  console.log(
    `OK · ${snap.computed_date} · ${snap.matches_played} partidos jugados · fase ${snap.phase}`
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
