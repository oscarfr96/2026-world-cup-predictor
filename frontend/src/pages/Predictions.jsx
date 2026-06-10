// Página principal: carga las predicciones (una lectura de la caché del backend), muestra el momento
// del modelo y deja navegar por todas las fases del Mundial (grupos → final) con un selector.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchPredictions } from "../lib/api.js";
import { phaseLabel } from "../lib/format.js";
import MatchCard from "../components/MatchCard.jsx";
import PendingRound from "../components/PendingRound.jsx";
import StageSelector from "../components/StageSelector.jsx";
import Loading from "../components/Loading.jsx";

function Chip({ children }) {
  return (
    <span className="rounded-full bg-white/80 px-3 py-1 text-sm font-medium text-slate-600 ring-1 ring-slate-200">
      {children}
    </span>
  );
}

export default function Predictions() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [activeKey, setActiveKey] = useState(null);

  useEffect(() => {
    fetchPredictions()
      .then((d) => {
        setData(d);
        if (d.rounds?.length) setActiveKey(d.rounds[0].key);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <div className="mb-3 text-4xl">😕</div>
        <h1 className="text-lg font-bold text-slate-700">No pudimos cargar las predicciones</h1>
        <p className="mt-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600">
          {error}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 rounded-full bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-sky-600"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data) return <Loading />;

  const activeRound = data.rounds.find((r) => r.key === activeKey) || data.rounds[0];

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      {/* Hero: momento del modelo + métricas (lo que pediste arriba) */}
      <section className="mb-6 rounded-3xl bg-white/70 p-6 ring-1 ring-slate-100 sm:p-8">
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-800 sm:text-3xl">
          Predictor del{" "}
          <span className="bg-gradient-to-r from-sky-500 via-violet-500 to-rose-500 bg-clip-text text-transparent">
            Mundial 2026
          </span>
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Un modelo que <strong className="text-slate-600">evoluciona durante el torneo</strong>.{" "}
          <Link to="/modelo" className="font-semibold text-sky-600 hover:underline">
            ¿Cómo funciona? →
          </Link>
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          <Chip>📊 {phaseLabel(data.phase)}</Chip>
          <Chip>🏟️ {data.matches_played} partidos jugados</Chip>
          <Link
            to="/historial"
            className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-200 transition hover:bg-emerald-100"
          >
            🎯 Ver mis aciertos →
          </Link>
        </div>
      </section>

      {/* Selector de fases */}
      <div className="sticky top-[57px] z-[5] -mx-4 bg-gradient-to-b from-white/80 to-transparent px-4 py-2 backdrop-blur-sm">
        <StageSelector rounds={data.rounds} activeKey={activeRound.key} onSelect={setActiveKey} />
      </div>

      {/* Contenido de la fase activa */}
      <div className="mt-4">
        {activeRound.pending ? (
          <PendingRound round={activeRound} />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {activeRound.matches.map((m, i) => (
              <MatchCard key={`${m.home}-${m.away}-${i}`} match={m} />
            ))}
          </div>
        )}
      </div>

      <p className="mt-8 text-center text-xs text-slate-400">
        Predicciones actualizadas una vez al día · {data.generated_at?.slice(0, 10)}
      </p>
    </div>
  );
}
