import { useEffect, useState } from "react";
import { getStatsSummary } from "../api/entries";
import type { StatsSummary } from "../types/entry";

interface StatCardProps {
  label: string;
  value: string | number;
  emoji: string;
}

function StatCard({ label, value, emoji }: StatCardProps) {
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

interface ListCardProps {
  title: string;
  items: string[];
  emoji: string;
}

function ListCard({ title, items, emoji }: ListCardProps) {
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

export default function Stats() {
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStatsSummary()
      .then(setStats)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Failed to load stats")
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-amber-600 text-lg animate-pulse">Loading stats…</div>
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

  if (!stats) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-800 mb-6">Your Stats</h1>

      {/* Count cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard label="This week" value={stats.weekly_count} emoji="📅" />
        <StatCard label="This month" value={stats.monthly_count} emoji="🗓️" />
        <StatCard
          label="Current streak"
          value={
            stats.current_streak_days === 1
              ? "1 day"
              : `${stats.current_streak_days} days`
          }
          emoji="🔥"
        />
      </div>

      {/* Top lists */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ListCard title="Top Types" items={stats.top_types} emoji="🎨" />
        <ListCard title="Top Names" items={stats.top_names} emoji="🏭" />
      </div>
    </div>
  );
}
