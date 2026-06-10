// Selector de fase/jornada. Scroll horizontal (no se apila en vertical ni tapa la vista en móvil).

import { roundLabel } from "../lib/format.js";

export default function StageSelector({ rounds, activeKey, onSelect }) {
  return (
    <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
      {rounds.map((r) => {
        const active = r.key === activeKey;
        return (
          <button
            key={r.key}
            onClick={() => onSelect(r.key)}
            className={`flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm font-semibold transition ${
              active
                ? "bg-gradient-to-r from-sky-500 to-violet-500 text-white shadow"
                : "bg-white/80 text-slate-500 ring-1 ring-slate-200 hover:bg-white hover:text-slate-700"
            }`}
          >
            {r.pending && <span className="text-xs">🔒</span>}
            {roundLabel(r)}
          </button>
        );
      })}
    </div>
  );
}
