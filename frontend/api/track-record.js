// Función serverless de Vercel: lee el track record persistido en Vercel Blob y lo sirve al frontend.
// El BLOB_READ_WRITE_TOKEN lo inyecta Vercel automáticamente al conectar el store de Blob al proyecto.

import { list } from "@vercel/blob";

const PATHNAME = "track-record.json";

export default async function handler(req, res) {
  try {
    const token = process.env.BLOB_READ_WRITE_TOKEN;
    if (!token) {
      // Aún no se ha conectado el store de Blob al proyecto → tratamos como "sin datos todavía".
      res.status(404).json({ detail: "Blob no configurado todavía." });
      return;
    }
    const { blobs } = await list({ prefix: PATHNAME, token });
    const hit = blobs.find((b) => b.pathname === PATHNAME);

    if (!hit) {
      res.status(404).json({ detail: "Aún no hay track record generado." });
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
    res.status(500).json({ detail: `No se pudo leer el track record: ${e}` });
  }
}
