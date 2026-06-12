import type { Feature, FeatureCollection } from "geojson";
import type { Layer } from "leaflet";
import { useEffect, useState } from "react";
import { GeoJSON } from "react-leaflet";
import type { ArrondissementStat } from "../../types/geo";

// amber-200 → amber-700: fill stepped by liters normalized to the top arrondissement
const AMBER_SCALE = ["#fde68a", "#fcd34d", "#fbbf24", "#f59e0b", "#d97706", "#b45309"];
const EMPTY_FILL = "#fffbeb"; // amber-50
const BORDER = "#92400e"; // amber-800

// fetched once per session — boundaries are immutable, no point re-fetching on view toggles
let shapesCache: FeatureCollection | null = null;

interface ArrondissementLayerProps {
  stats: ArrondissementStat[];
}

function ordinal(arrondissement: number): string {
  return arrondissement === 1 ? "1er" : `${arrondissement}e`;
}

export default function ArrondissementLayer({ stats }: ArrondissementLayerProps) {
  const [shapes, setShapes] = useState<FeatureCollection | null>(shapesCache);

  useEffect(() => {
    if (shapesCache) return;
    fetch("/paris-arrondissements.geojson")
      .then((r) => r.json())
      .then((data: FeatureCollection) => {
        shapesCache = data;
        setShapes(data);
      });
  }, []);

  if (!shapes) return null;

  const statsByArrondissement = new Map(stats.map((s) => [s.arrondissement, s]));
  const maxLiters = Math.max(...stats.map((s) => s.total_liters), 0);

  const style = (feature?: Feature) => {
    const stat = statsByArrondissement.get(feature?.properties?.c_ar);
    if (!stat || maxLiters === 0) {
      return { color: BORDER, weight: 1, fillColor: EMPTY_FILL, fillOpacity: 0.2 };
    }
    const index = Math.min(
      Math.floor((stat.total_liters / maxLiters) * AMBER_SCALE.length),
      AMBER_SCALE.length - 1,
    );
    return { color: BORDER, weight: 1.5, fillColor: AMBER_SCALE[index], fillOpacity: 0.55 };
  };

  const onEachFeature = (feature: Feature, layer: Layer) => {
    const arrondissement = feature.properties?.c_ar as number;
    const stat = statsByArrondissement.get(arrondissement);
    const detail = stat
      ? `🍺 ${stat.total_liters} L · ${stat.entry_count} ${stat.entry_count > 1 ? "beers" : "beer"}`
      : "Nothing drunk here yet";
    layer.bindPopup(`<b>${ordinal(arrondissement)}</b><br/>${detail}`);
  };

  // react-leaflet's GeoJSON caches style/popups at mount — remount when the stats change
  return <GeoJSON key={JSON.stringify(stats)} data={shapes} style={style} onEachFeature={onEachFeature} />;
}
