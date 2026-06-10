import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Servidor de desarrollo en http://localhost:5173 (espera el backend en VITE_API_BASE).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
