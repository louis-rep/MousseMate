import { useEffect, useState } from "react";
import { searchBars } from "../api/bars";
import type { Bar } from "../types/bar";

interface Props {
  selected: Bar | null;
  onSelect: (bar: Bar | null) => void;
}

function barHint(bar: Bar): string {
  const parts = [bar.address, bar.postcode].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : bar.amenity;
}

export default function BarAutocomplete({ selected, onSelect }: Props) {
  const [query, setQuery] = useState(selected?.name ?? "");
  const [suggestions, setSuggestions] = useState<Bar[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2 || (selected && q === selected.name)) {
      setSuggestions([]);
      return;
    }
    const handle = window.setTimeout(async () => {
      try {
        setSuggestions(await searchBars(q));
        setOpen(true);
      } catch {
        setSuggestions([]);
      }
    }, 250);
    return () => window.clearTimeout(handle);
  }, [query, selected]);

  function handleInput(e: React.ChangeEvent<HTMLInputElement>) {
    setQuery(e.target.value);
    if (selected) onSelect(null); // typing again invalidates the previous selection
  }

  function handleSelect(bar: Bar) {
    onSelect(bar);
    setQuery(bar.name);
    setOpen(false);
  }

  return (
    <div className="relative">
      <input
        id="bar"
        name="bar"
        type="text"
        required
        autoComplete="off"
        value={query}
        onChange={handleInput}
        onFocus={() => suggestions.length > 0 && setOpen(true)}
        onBlur={() => setOpen(false)}
        placeholder="Search a bar in Paris…"
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
      />
      {open && suggestions.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full max-h-56 overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg text-sm">
          {suggestions.map((bar) => (
            <li key={bar.id}>
              {/* onMouseDown fires before the input's onBlur, so the click isn't swallowed */}
              <button
                type="button"
                onMouseDown={() => handleSelect(bar)}
                className="w-full text-left px-3 py-2 hover:bg-amber-50"
              >
                <span className="font-medium text-gray-800">{bar.name}</span>
                <span className="ml-2 text-xs text-gray-400">{barHint(bar)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
