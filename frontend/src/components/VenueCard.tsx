import type { Venue } from "../types/entry";
import EntryCard from "./EntryCard";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { dateStyle: "long" });
}

export default function VenueCard({ venue }: { venue: Venue }) {
  return (
    <div className="bg-amber-50 rounded-2xl shadow-md border border-amber-200 p-5 flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div>
          <p className="font-bold text-amber-800 text-base">{venue.bar}</p>
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
