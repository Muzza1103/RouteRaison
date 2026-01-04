import { MapContainer, Marker, Popup, TileLayer, GeoJSON as LeafletGeoJSON } from "react-leaflet";
import type { Feature } from "geojson";
import type { LatLon, PlanResponse } from "../../types/routeraison";
import { MapClickPicker } from "./MapClickPicker";
import { FitBoundsToGeoJSON } from "./FitBoundsToGeoJSON";

type Props = {
  origin?: LatLon;
  destination?: LatLon;
  picking: "ORIGIN" | "DESTINATION";
  onPick: (which: "ORIGIN" | "DESTINATION", lat: number, lon: number) => void;

  plan?: PlanResponse | null;
};

export function MapView({ origin, destination, picking, onPick, plan }: Props) {
  const center: [number, number] = origin ? [origin.lat, origin.lon] : [48.8566, 2.3522];

  const geometry = plan?.route?.geometry;
  const feature: Feature | null = geometry
    ? { type: "Feature", properties: {}, geometry: geometry as any }
    : null;

  const station = plan?.route?.debug_station ?? null;

  return (
    <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapClickPicker
        enabled={true}
        onPick={(lat, lon) => onPick(picking, lat, lon)}
      />

      {origin && (
        <Marker position={[origin.lat, origin.lon]}>
          <Popup>Origine</Popup>
        </Marker>
      )}

      {destination && (
        <Marker position={[destination.lat, destination.lon]}>
          <Popup>Destination</Popup>
        </Marker>
      )}

      {station && (
        <Marker position={[station.lat, station.lon]}>
          <Popup>
            Station essence<br />
            <b>{station.name}</b>
          </Popup>
        </Marker>
      )}

      {feature && (
        <>
          <LeafletGeoJSON data={feature as any} />
          <FitBoundsToGeoJSON geo={feature} />
        </>
      )}
    </MapContainer>
  );
}