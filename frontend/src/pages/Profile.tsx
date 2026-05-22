import { useEffect, useState } from "react";
import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
const Plot = createPlotlyComponent(Plotly as Parameters<typeof createPlotlyComponent>[0]);
import { useParams } from "react-router-dom";
import { getStatsSummary, listEntries } from "../api/entries";
import { getUser } from "../api/follow";
import LogBeerModal from "../components/LogBeerModal";
import VenueCard from "../components/VenueCard";
import { useAuth } from "../hooks/useAuth";
import type { StatsSummary, Venue } from "../types/entry";
import type { UserRead } from "../types/auth";

function StatCard({ label, value, emoji }: { label: string; value: string | number; emoji: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-5 flex items-center gap-4">
      <span className="text-3xl">{emoji}</span>
      <div>
        <p className="text-2xl font-bold text-amber-700">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}

function ListCard({ title, items, emoji }: { title: string; items: string[]; emoji: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-5">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        {emoji} {title}
      </h3>
      {items.length === 0 ? (
        <p className="text-sm text-gray-400 italic">No data yet</p>
      ) : (
        <ol className="space-y-1">
          {items.map((item, i) => (
            <li key={item} className="flex items-center gap-2 text-sm text-gray-700">
              <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-700 text-xs font-bold flex items-center justify-center">
                {i + 1}
              </span>
              {item}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

export default function Profile() {
  const { userId: userIdParam } = useParams<{ userId: string }>();
  const userId = parseInt(userIdParam ?? "0", 10);
  const { userId: currentUserId } = useAuth();
  const isOwnProfile = userId === currentUserId;

  const [user, setUser] = useState<UserRead | null>(null);
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([getUser(userId), getStatsSummary(userId), listEntries(userId)])
      .then(([u, s, v]) => {
        setUser(u);
        setStats(s);
        setVenues(v);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load profile"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (userId) load();
  }, [userId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-amber-600 text-lg animate-pulse">Loading…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-lg bg-red-100 border border-red-300 text-red-800 text-sm">
        Error: {error}
      </div>
    );
  }

  if (!stats || !user) return null;

  const totalBeers = venues.reduce((sum, v) => sum + v.entries.length, 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-amber-800">{user.username}</h1>
        {isOwnProfile && (
          <button
            onClick={() => setModalOpen(true)}
            className="bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            + Log a beer
          </button>
        )}
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard label="This week" value={stats.weekly_count} emoji="📅" />
        <StatCard label="This month" value={stats.monthly_count} emoji="🗓️" />
        <StatCard label="Total drunk" value={`${stats.total_liters} L`} emoji="🍺" />
      </div>

      {/* Top lists */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <ListCard title="Top Types" items={stats.top_types} emoji="🎨" />
        <ListCard title="Top Names" items={stats.top_names} emoji="🏭" />
      </div>

      {/* Charts */}
      <div className="hidden sm:flex flex-col gap-4 mb-6">
        <div className="bg-white rounded-2xl shadow-md p-5">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            📈 Daily consumption — last 7 days
          </h3>
          <Plot
            data={stats.daily_liters.map((series) => ({
              type: "bar" as const,
              name: series.type,
              x: series.daily.map((d) => d.date),
              y: series.daily.map((d) => d.liters),
            }))}
            layout={{ barmode: "stack", xaxis: { type: "date" }, yaxis: { title: { text: "Liters" } }, margin: { t: 10, r: 10, b: 40, l: 50 }, plot_bgcolor: "transparent", paper_bgcolor: "transparent", autosize: true }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%" }}
            useResizeHandler
          />
        </div>

        <div className="bg-white rounded-2xl shadow-md p-5">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            🎨 Liters by style (all time)
          </h3>
          <Plot
            data={stats.liters_by_type.map((series) => ({
              type: "bar" as const,
              name: series.bar ?? "No bar",
              x: series.values.map((v) => v.type),
              y: series.values.map((v) => v.liters),
            }))}
            layout={{ barmode: "stack", yaxis: { title: { text: "Liters" } }, margin: { t: 10, r: 10, b: 60, l: 50 }, plot_bgcolor: "transparent", paper_bgcolor: "transparent", autosize: true }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%" }}
            useResizeHandler
          />
        </div>
      </div>

      {/* Beer list */}
      {totalBeers === 0 ? (
        <p className="text-center text-gray-400 italic py-16">No beers logged yet.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {venues.map((venue, i) => (
            <VenueCard key={i} venue={venue} />
          ))}
        </div>
      )}

      {modalOpen && (
        <LogBeerModal onClose={() => setModalOpen(false)} onSuccess={() => { setModalOpen(false); load(); }} />
      )}
    </div>
  );
}
