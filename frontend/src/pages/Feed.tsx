import { useEffect, useState } from "react";
import { listEntries } from "../api/entries";
import LogBeerModal from "../components/LogBeerModal";
import VenueCard from "../components/VenueCard";
import type { Venue } from "../types/entry";

export default function Feed() {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  function load() {
    setLoading(true);
    listEntries()
      .then(setVenues)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load feed"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  const totalBeers = venues.reduce((sum, v) => sum + v.entries.length, 0);

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-amber-800">Feed</h1>
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
        <p className="text-center text-gray-400 italic py-24">Nothing here yet. Follow some mates or log your first beer.</p>
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
