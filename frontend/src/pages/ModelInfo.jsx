// Página "Cómo funciona": explicación sencilla y visual del modelo, sin fórmulas intimidantes.

import { Link } from "react-router-dom";
import { REPO_URL } from "../lib/format.js";
import GitHubIcon from "../components/GitHubIcon.jsx";

function Step({ emoji, title, children }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-2xl">{emoji}</span>
        <h3 className="text-base font-bold text-slate-800">{title}</h3>
      </div>
      <p className="text-sm leading-relaxed text-slate-600">{children}</p>
    </div>
  );
}

export default function ModelInfo() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-extrabold tracking-tight text-slate-800 sm:text-3xl">
        ¿Cómo funciona el{" "}
        <span className="bg-gradient-to-r from-sky-500 via-violet-500 to-rose-500 bg-clip-text text-transparent">
          predictor
        </span>
        ?
      </h1>
      <p className="mt-2 text-slate-600">
        La idea es sencilla: estimar cuántos goles marcará cada selección y, a partir de ahí, calcular
        quién gana y con qué marcador. Lo bonito es que el modelo <strong>aprende</strong> a medida que se
        juega el torneo.
      </p>

      {/* Las dos fases */}
      <h2 className="mt-8 text-lg font-bold text-slate-800">El truco: dos fases</h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-sky-100 bg-sky-50/60 p-5">
          <div className="mb-1 text-sm font-bold uppercase tracking-wide text-sky-600">Fase 1 · antes</div>
          <p className="text-sm leading-relaxed text-slate-600">
            El modelo llega <strong>pre-entrenado</strong> con los partidos internacionales recientes de
            cada selección (clasificación, Nations League, amistosos…). Así, antes de que ruede el balón,
            ya tiene una estimación <em>objetiva</em> de su ataque y su defensa — nada de cold start.
          </p>
        </div>
        <div className="rounded-2xl border border-violet-100 bg-violet-50/60 p-5">
          <div className="mb-1 text-sm font-bold uppercase tracking-wide text-violet-600">
            Fase 2 · durante
          </div>
          <p className="text-sm leading-relaxed text-slate-600">
            En cuanto hay partidos del Mundial, el modelo <strong>reajusta</strong> la fuerza de cada
            equipo con los goles que marca y encaja <em>en el propio torneo</em>, mezclándolos con lo que
            ya sabía. Cuanto más se juega, más mandan los datos del Mundial.
          </p>
        </div>
      </div>

      {/* Pasos */}
      <h2 className="mt-8 text-lg font-bold text-slate-800">Paso a paso</h2>
      <div className="mt-3 space-y-3">
        <Step emoji="⚽" title="1. Goles esperados">
          Para cada equipo se estima un número de goles esperado combinando <strong>su ataque</strong> y{" "}
          <strong>la defensa del rival</strong>: un ataque fuerte contra una defensa floja = más goles
          esperados. Como el Mundial se juega en sede neutral no hay ventaja de local… salvo para las
          <strong> anfitrionas (EE. UU., Canadá y México)</strong>, que sí juegan en casa y reciben un
          pequeño plus.
        </Step>
        <Step emoji="🎲" title="2. De goles a probabilidades">
          Con esos goles esperados, una distribución de <strong>Poisson</strong> (la matemática clásica
          para contar sucesos, como goles) calcula la probabilidad de cada marcador posible. Sumándolos
          salen las probabilidades de victoria, empate y derrota, el favorito y los marcadores más
          probables.
        </Step>
        <Step emoji="⚖️" title="3. No fiarse de pocos partidos">
          Que una selección gane 3-0 su primer partido no la convierte en campeona. Por eso lo aprendido
          en el Mundial se <strong>mezcla</strong> con el nivel previo (el de los internacionales): al
          principio manda el prior, y conforme se acumulan partidos, mandan los datos del torneo. (En
          estadística esto se llama <em>shrinkage</em>.)
        </Step>
        <Step emoji="🎯" title="4. ¿Acierta?">
          Cada día, para los partidos ya jugados, se compara el favorito que predijo el modelo con el
          resultado real. Ese porcentaje de acierto se muestra en la portada, sin trampa ni cartón.
        </Step>
      </div>

      <div className="mt-8 rounded-2xl bg-white/70 p-5 text-center ring-1 ring-slate-100">
        <p className="text-sm text-slate-600">
          Todo el código es abierto y está comentado paso a paso.
        </p>
        <a
          href={REPO_URL}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-flex items-center gap-2 rounded-full bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
        >
          <GitHubIcon /> Ver el código en GitHub
        </a>
      </div>

      <div className="mt-6 text-center">
        <Link to="/" className="text-sm font-semibold text-sky-600 hover:underline">
          ← Volver a las predicciones
        </Link>
      </div>
    </div>
  );
}
