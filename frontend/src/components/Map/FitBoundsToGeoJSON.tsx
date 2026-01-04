import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";

type AnyGeo = Feature | FeatureCollection | Geometry;

export function FitBoundsToGeoJSON({ geo }: { geo?: AnyGeo | null }) {
  const map = useMap();

  useEffect(() => {
    if (!geo) return;
    try {
      const layer = L.geoJSON(geo as any);
      const bounds = layer.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds.pad(0.2));
    } catch {
      // ignore
    }
  }, [geo, map]);

  return null;
}