import { useEffect, useState } from "react";

// Mensajes que van rotando mientras se despierta el backend (free tier de Render = siesta).
const MESSAGES = [
  "Despertando el servidor… el free tier de Render estaba echándose la siesta 😴",
  "Esto tarda lo que el VAR en revisar un fuera de juego milimétrico ⏳",
  "Pidiendo los datos del Mundial entero, dame un segundito 🌍",
  "Lo barato sale caro… en latencia. ¡Ya casi! 🐢",
  "Calentando en la banda antes de saltar al campo ⚽",
  "Montando las predicciones, no te vayas que viene lo bueno 🔮",
];

export default function Loading() {
  const [i, setI] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setI((p) => (p + 1) % MESSAGES.length), 2600);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center gap-7 px-6 py-24 text-center">
      <div className="text-6xl animate-kick">⚽</div>

      {/* Barra de progreso indeterminada */}
      <div className="h-2 w-44 overflow-hidden rounded-full bg-white/70 shadow-inner">
        <div className="h-full w-1/3 rounded-full bg-gradient-to-r from-sky-400 via-violet-400 to-rose-400 animate-loadbar" />
      </div>

      {/* El key fuerza la animación de entrada en cada mensaje nuevo */}
      <p key={i} className="max-w-xs animate-fade-in-up text-base font-medium text-slate-600">
        {MESSAGES[i]}
      </p>

      <p className="text-xs text-slate-400">La primera carga del día puede tardar ~30-50 s. Las siguientes van al vuelo.</p>
    </div>
  );
}
