import L from "leaflet";

// @ts-ignore
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
// @ts-ignore
import iconUrl from "leaflet/dist/images/marker-icon.png";
// @ts-ignore
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});