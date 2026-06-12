import { CircleMarker, Popup } from "react-leaflet";
import type { VenueMapPoint } from "../../types/geo";

interface VenueMarkerProps {
  venue: VenueMapPoint;
}

// sqrt scale so a venue with 4x the liters reads as 2x the pin, clamped for legibility
function pinRadius(liters: number): number {
  return Math.min(8 + Math.sqrt(liters) * 6, 26);
}

function formatLastVisit(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export default function VenueMarker({ venue }: VenueMarkerProps) {
  const colors = venue.is_closed
    ? { color: "#6b7280", fillColor: "#9ca3af" }
    : { color: "#b45309", fillColor: "#f59e0b" };

  return (
    <CircleMarker
      center={[venue.latitude, venue.longitude]}
      radius={pinRadius(venue.total_liters)}
      pathOptions={{ ...colors, weight: 2, fillOpacity: 0.7 }}
    >
      <Popup>
        <div className="min-w-48">
          <p className="font-bold text-amber-800 text-sm !my-0">
            {venue.name}
            {venue.is_closed && <span className="ml-2 text-xs font-medium text-gray-500">(closed)</span>}
          </p>
          {venue.address && <p className="text-xs text-gray-500 !my-0">{venue.address}</p>}
          <p className="text-xs text-gray-600 !mt-1 !mb-0">
            🍺 {venue.total_liters} L · {venue.entry_count} {venue.entry_count > 1 ? "beers" : "beer"} · last visit{" "}
            {formatLastVisit(venue.last_visit)}
          </p>
          <div className="flex flex-wrap gap-1 !mt-2">
            {venue.drinkers.map((d) => (
              <span
                key={d.username}
                className="text-xs font-semibold bg-amber-50 border border-amber-200 text-amber-800 px-2 py-0.5 rounded-full"
              >
                {d.username} — {d.liters} L
              </span>
            ))}
          </div>
        </div>
      </Popup>
    </CircleMarker>
  );
}
