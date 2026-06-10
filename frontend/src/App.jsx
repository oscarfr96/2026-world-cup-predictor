// Layout de la app: cabecera con navegación, rutas (predicciones / cómo funciona) y pie con créditos.

import { Routes, Route, NavLink, Link } from "react-router-dom";
import Predictions from "./pages/Predictions.jsx";
import ModelInfo from "./pages/ModelInfo.jsx";
import Today from "./pages/Today.jsx";
import TrackRecord from "./pages/TrackRecord.jsx";
import GitHubIcon from "./components/GitHubIcon.jsx";
import { REPO_URL } from "./lib/format.js";

function navClass({ isActive }) {
  return `rounded-full px-3 py-1.5 text-sm font-semibold transition ${
    isActive ? "bg-sky-500 text-white shadow" : "text-slate-500 hover:bg-white hover:text-slate-700"
  }`;
}

function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-100 bg-white/75 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-4 py-2.5">
        <Link to="/" aria-label="Inicio" className="flex items-center gap-2 text-2xl font-extrabold">
          <span>⚽</span>
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={navClass}>
            Predicciones
          </NavLink>
          <NavLink to="/historial" className={navClass}>
            Aciertos
          </NavLink>
          <NavLink to="/modelo" className={navClass}>
            Cómo funciona
          </NavLink>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            aria-label="Código en GitHub"
            className="ml-1 rounded-full p-2 text-slate-500 transition hover:bg-white hover:text-slate-800"
          >
            <GitHubIcon className="h-5 w-5" />
          </a>
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-10 border-t border-slate-100 bg-white/50">
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-1 px-4 py-6 text-center text-sm text-slate-500">
        <p>
          Hecho por{" "}
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 font-semibold text-slate-700 hover:text-sky-600"
          >
            <GitHubIcon className="h-4 w-4" /> Óscar
          </a>{" "}
          · proyecto abierto de ML/estadística
        </p>
        <p className="text-xs text-slate-400">
          Datos de football-data.org · no es una herramienta de apuestas
        </p>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Predictions />} />
          <Route path="/historial" element={<TrackRecord />} />
          <Route path="/modelo" element={<ModelInfo />} />
          {/* Página "oculta" para vídeos (no enlazada en la navegación). */}
          <Route path="/today" element={<Today />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
