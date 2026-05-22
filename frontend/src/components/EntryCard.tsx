import type { Entry } from "../types/entry";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { timeStyle: "short" });
}

export default function EntryCard({ entry }: { entry: Entry }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-amber-100 p-4 flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <div>
          {entry.username && (
            <p className="text-xs text-amber-500 font-medium mb-1">@{entry.username}</p>
          )}
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
