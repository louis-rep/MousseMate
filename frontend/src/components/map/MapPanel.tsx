import { useState } from "react";
import type { MapScope } from "../../types/geo";

export type MapView = "bars" | "heatmap";

const SCOPES: { value: MapScope; label: string }[] = [
  { value: "me", label: "Me" },
  { value: "mates", label: "My mates" },
];

const VIEWS: { value: MapView; label: string }[] = [
  { value: "bars", label: "Bars" },
  { value: "heatmap", label: "Heatmap" },
];

interface MapPanelProps {
  view: MapView;
  onViewChange: (view: MapView) => void;
  scope: MapScope;
  onScopeChange: (scope: MapScope) => void;
}

function SectionLabel({ children }: { children: string }) {
  return <p className="text-xs font-semibold uppercase tracking-wide text-amber-400 mb-1.5">{children}</p>;
}

const activeClass = "bg-amber-600 text-white";
const inactiveClass = "text-amber-800 hover:bg-amber-50";
const buttonClass = "text-left text-sm font-semibold px-3 py-1.5 rounded-lg transition-colors";

function ViewButtons({ view, onViewChange }: Pick<MapPanelProps, "view" | "onViewChange">) {
  return (
    <>
      {VIEWS.map((v) => (
        <button
          key={v.value}
          onClick={() => onViewChange(v.value)}
          className={`${buttonClass} ${view === v.value ? activeClass : inactiveClass}`}
        >
          {v.label}
        </button>
      ))}
      <button
        disabled
        title="Coming soon"
        className={`${buttonClass} flex items-center justify-between gap-2 text-gray-400 cursor-not-allowed`}
      >
        Arrondissement
        <span className="text-[10px] font-medium bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">soon</span>
      </button>
    </>
  );
}

function ScopeButtons({ scope, onScopeChange }: Pick<MapPanelProps, "scope" | "onScopeChange">) {
  return (
    <>
      {SCOPES.map((s) => (
        <button
          key={s.value}
          onClick={() => onScopeChange(s.value)}
          className={`${buttonClass} ${scope === s.value ? activeClass : inactiveClass}`}
        >
          {s.label}
        </button>
      ))}
    </>
  );
}

export default function MapPanel({ view, onViewChange, scope, onScopeChange }: MapPanelProps) {
  const [sheetOpen, setSheetOpen] = useState(false);
  const viewLabel = VIEWS.find((v) => v.value === view)?.label;
  const scopeLabel = SCOPES.find((s) => s.value === scope)?.label;

  return (
    <>
      {/* Desktop: floating left card */}
      <div className="hidden sm:flex absolute top-4 left-4 z-[1000] w-44 bg-white rounded-xl border border-amber-100 shadow-lg p-3 flex-col gap-3">
        <div>
          <SectionLabel>View</SectionLabel>
          <div className="flex flex-col gap-1">
            <ViewButtons view={view} onViewChange={onViewChange} />
          </div>
        </div>
        <div>
          <SectionLabel>Who</SectionLabel>
          <div className="flex flex-col gap-1">
            <ScopeButtons scope={scope} onScopeChange={onScopeChange} />
          </div>
        </div>
      </div>

      {/* Mobile: collapsible bottom sheet */}
      <div className="sm:hidden absolute inset-x-0 bottom-0 z-[1000] bg-white rounded-t-2xl shadow-[0_-2px_12px_rgba(0,0,0,0.12)] pb-[env(safe-area-inset-bottom)]">
        <button
          onClick={() => setSheetOpen((o) => !o)}
          aria-expanded={sheetOpen}
          className="w-full flex flex-col items-center gap-1 pt-2 pb-2"
        >
          <span className="h-1 w-10 rounded-full bg-amber-200" />
          <span className="flex items-center gap-1.5 text-xs font-semibold text-amber-800">
            {viewLabel} · {scopeLabel}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className={`h-3.5 w-3.5 transition-transform ${sheetOpen ? "rotate-180" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </span>
        </button>
        {sheetOpen && (
          <div className="px-4 pb-4 flex flex-col gap-3">
            <div>
              <SectionLabel>View</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                <ViewButtons view={view} onViewChange={onViewChange} />
              </div>
            </div>
            <div>
              <SectionLabel>Who</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                <ScopeButtons scope={scope} onScopeChange={onScopeChange} />
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
