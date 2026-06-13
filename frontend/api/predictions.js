// Función serverless de Vercel: lee el snapshot de predicciones persistido en Vercel Blob y lo sirve.
// Así la web no depende del disco efímero ni del uptime del backend en Render (que al reciclarse
// vuelve a la semilla vieja). El BLOB_READ_WRITE_TOKEN lo inyecta Vercel al conectar el store de Blob.

import { list } from "@vercel/blob";

const PATHNAME = "predictions.json";

export default async function handler(req, res) {
  try {
    const token = process.env.BLOB_READ_WRITE_TOKEN;
    if (!token) {
      // Aún no se ha conectado el store de Blob → 404 para que el frontend caiga al backend (fallback).
      res.status(404).json({ detail: "Blob no configurado todavía." });
      return;
    }
    const { blobs } = await list({ prefix: PATHNAME, token });
    const hit = blobs.find((b) => b.pathname === PATHNAME);

    if (!hit) {
      res.status(404).json({ detail: "Aún no hay predicciones publicadas en Blob." });
      return;
    }

    // Store privado → la URL del blob requiere autenticación con el token.
    const r = await fetch(hit.url, {
      cache: "no-store",
      headers: { authorization: `Bearer ${token}` },
    });
    const data = await r.json();

    // Cambia como mucho 1 vez/día → se puede cachear un rato en el edge.
    res.setHeader("Cache-Control", "public, max-age=300, s-maxage=900");
    res.status(200).json(data);
  } catch (e) {
    res.status(500).json({ detail: `No se pudieron leer las predicciones: ${e}` });
  }
}
