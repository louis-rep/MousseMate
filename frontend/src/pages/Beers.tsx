import { useEffect, useState } from "react";
import { listEntries } from "../api/entries";
import LogBeerModal from "../components/LogBeerModal";
import type { Entry } from "../types/entry";

function formatDatetime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function EntryCard({ entry }: { entry: Entry }) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-5 flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-gray-800 text-base">
            {entry.name ?? <span className="text-gray-400 italic">Unknown</span>}
          </p>
          <span className="inline-block mt-1 text-xs font-medium bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
            {entry.type}
          </span>
        </div>
        {entry.rating !== null && (
          <span className="text-amber-600 font-bold text-lg shrink-0">★ {entry.rating}</span>
        )}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
        <span>{entry.volume} ml</span>
        {entry.bar && <span>📍 {entry.bar}</span>}
        <span>🕐 {formatDatetime(entry.drink_datetime)}</span>
      </div>

      {entry.notes && <p className="text-sm text-gray-600 italic border-t pt-2 mt-1">{entry.notes}</p>}
    </div>
  );
}

export default function Beers() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  function load() {
    setLoading(true);
    listEntries(0, 100)
      .then(setEntries)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load entries"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-amber-800">My Beers</h1>
        <button
          onClick={() => setModalOpen(true)}
          className="bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          + Log a beer
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-24">
          <div className="text-amber-600 text-lg animate-pulse">Loading…</div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-100 border border-red-300 text-red-800 text-sm">Error: {error}</div>
      )}

      {!loading && !error && entries.length === 0 && (
        <p className="text-center text-gray-400 italic py-24">No beers logged yet. Time to fix that.</p>
      )}

      <div className="flex flex-col gap-4">
        {entries.map((entry) => (
          <EntryCard key={entry.id} entry={entry} />
        ))}
      </div>

      {modalOpen && (
        <LogBeerModal onClose={() => setModalOpen(false)} onSuccess={load} />
      )}
    </>
  );
}
