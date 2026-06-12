import L from "leaflet";
import "leaflet.heat";
import { useEffect } from "react";
import { useMap } from "react-leaflet";
import type { VenueMapPoint } from "../../types/geo";

interface HeatLayerProps {
  venues: VenueMapPoint[];
}

export default function HeatLayer({ venues }: HeatLayerProps) {
  const map = useMap();

  useEffect(() => {
    if (venues.length === 0) return;
    const maxLiters = Math.max(...venues.map((v) => v.total_liters));
    const points = venues.map(
      (v) => [v.latitude, v.longitude, v.total_liters / maxLiters] as [number, number, number],
    );
    const layer = L.heatLayer(points, { radius: 35, blur: 25, maxZoom: 17 });
    layer.addTo(map);
    return () => {
      map.removeLayer(layer);
    };
  }, [map, venues]);

  return null;
}
