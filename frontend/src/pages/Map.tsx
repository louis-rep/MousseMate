import { useEffect, useState } from "react";
import { AttributionControl, MapContainer, TileLayer, ZoomControl, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { getVenueMap } from "../api/geo";
import MapPanel from "../components/map/MapPanel";
import VenueMarker from "../components/map/VenueMarker";
import type { MapScope, VenueMapPoint, VenueMapResponse } from "../types/geo";

const PARIS_CENTER: [number, number] = [48.8566, 2.3522];

function FitBounds({ venues }: { venues: VenueMapPoint[] }) {
  const map = useMap();
  useEffect(() => {
    if (venues.length === 0) return;
    map.fitBounds(
      venues.map((v) => [v.latitude, v.longitude] as [number, number]),
      { padding: [40, 40], maxZoom: 16 },
    );
  }, [map, venues]);
  return null;
}

export default function MapPage() {
  const [scope, setScope] = useState<MapScope>("mates");
  const [data, setData] = useState<VenueMapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stale = false;
    setError(null);
    getVenueMap(scope)
      .then((response) => {
        if (!stale) setData(response);
      })
      .catch((err: unknown) => {
        if (!stale) setError(err instanceof Error ? err.message : "Failed to load the map");
      });
    return () => {
      stale = true;
    };
  }, [scope]);

  return (
    <div className="relative z-0 h-full w-full">
      <MapContainer
        center={PARIS_CENTER}
        zoom={13}
        zoomControl={false}
        attributionControl={false}
        className="h-full w-full"
      >
        <ZoomControl position="topright" />
        {/* top-right, not bottom: the mobile bottom sheet would cover it, and OSM/CARTO require visible attribution */}
        <AttributionControl position="topright" />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        {data?.venues.map((v) => (
          <VenueMarker key={v.bar_id} venue={v} />
        ))}
        {data && <FitBounds venues={data.venues} />}
      </MapContainer>
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg shadow">
          {error}
        </div>
      )}
      {data && data.venues.length === 0 && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white border border-amber-200 text-amber-800 text-sm px-4 py-2 rounded-lg shadow">
          No venues yet — log a beer to put it on the map!
        </div>
      )}
      <MapPanel scope={scope} onScopeChange={setScope} />
    </div>
  );
}
