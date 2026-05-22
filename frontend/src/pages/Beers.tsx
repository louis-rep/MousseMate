import { useEffect, useState } from "react";
import { listEntries } from "../api/entries";
import LogBeerModal from "../components/LogBeerModal";
import type { Entry, Venue } from "../types/entry";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { dateStyle: "long" });
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { timeStyle: "short" });
}

function EntryCard({ entry }: { entry: Entry }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-amber-100 p-4 flex flex-col gap-2">
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
        <span>🕐 {formatTime(entry.drink_datetime)}</span>
      </div>

      {entry.notes && <p className="text-sm text-gray-600 italic border-t pt-2 mt-1">{entry.notes}</p>}
    </div>
  );
}

function VenueCard({ venue }: { venue: Venue }) {
  return (
    <div className="bg-amber-50 rounded-2xl shadow-md border border-amber-200 p-5 flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div>
          <p className="font-bold text-amber-800 text-base">{venue.bar ?? <span className="italic text-amber-500">No bar</span>}</p>
          <p className="text-sm text-amber-600">{formatDate(venue.date)}</p>
        </div>
        <span className="ml-auto text-xs text-amber-500 font-medium">
          {venue.entries.length} {venue.entries.length === 1 ? "beer" : "beers"}
        </span>
      </div>
      <div className="flex flex-col gap-2">
        {venue.entries.map((entry) => (
          <EntryCard key={entry.id} entry={entry} />
        ))}
      </div>
    </div>
  );
}

export default function Beers() {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  function load() {
    setLoading(true);
    listEntries()
      .then(setVenues)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load entries"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  const totalBeers = venues.reduce((sum, v) => sum + v.entries.length, 0);

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-amber-800">Your Beers</h1>
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

      {!loading && !error && totalBeers === 0 && (
        <p className="text-center text-gray-400 italic py-24">No beers logged yet. Time to fix that.</p>
      )}

      <div className="flex flex-col gap-4">
        {venues.map((venue, i) => (
          <VenueCard key={i} venue={venue} />
        ))}
      </div>

      {modalOpen && <LogBeerModal onClose={() => setModalOpen(false)} onSuccess={load} />}
    </>
  );
}
