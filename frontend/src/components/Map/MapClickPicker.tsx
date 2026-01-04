import { useMapEvents } from "react-leaflet";

export function MapClickPicker(props: {
  enabled: boolean;
  onPick: (lat: number, lon: number) => void;
}) {
  useMapEvents({
    click(e) {
      if (!props.enabled) return;
      props.onPick(e.latlng.lat, e.latlng.lng);
    },
  });

  return null;
}