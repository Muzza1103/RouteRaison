from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
import httpx


@dataclass(frozen=True)
class OrsRoute:
    distance_m: float
    duration_s: float
    geometry: Any
    raw: Dict[str, Any]


class ORSRoutingService:
    """
    ORS routing service that supports:
      - 2 points (origin -> destination)
      - 3+ points (origin -> waypoint(s) -> destination) ex: refuel
      - composable constraints: preference + avoid_features
    """

    def __init__(self, api_key: Optional[str] = None, timeout_s: float = 15.0):
        self.api_key = api_key or os.getenv("ORS_API_KEY")
        if not self.api_key:
            raise RuntimeError("ORS_API_KEY is missing (env var).")
        self.timeout_s = timeout_s
        self.base_url = os.getenv("ORS_BASE_URL", "https://api.openrouteservice.org")

    async def get_route_with_coords(
        self,
        coords: List[List[float]],
        preference: str = "fastest",                   # "fastest" | "shortest" | "recommended"
        avoid_features: Optional[List[str]] = None,    # e.g. ["highways","tollways"]
    ) -> OrsRoute:
        url = f"{self.base_url}/v2/directions/driving-car/geojson"
        headers = {"Authorization": self.api_key, "Content-Type": "application/json"}

        body: Dict[str, Any] = {
            "coordinates": coords,
            "instructions": False,
            "preference": preference,
        }

        if avoid_features:
            # ORS expects a list of strings
            body["options"] = {"avoid_features": sorted(set(avoid_features))}

        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()

        features = data.get("features") or []
        if not features:
            raise RuntimeError("ORS response has no features.")

        f0 = features[0]
        summary = (f0.get("properties") or {}).get("summary") or {}
        distance_m = float(summary.get("distance") or 0.0)
        duration_s = float(summary.get("duration") or 0.0)
        geometry = f0.get("geometry")

        return OrsRoute(distance_m=distance_m, duration_s=duration_s, geometry=geometry, raw=data)

    async def get_route(
        self,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float,
        preference: str = "fastest",
        avoid_features: Optional[List[str]] = None,
    ) -> OrsRoute:
        coords = [[origin_lon, origin_lat], [dest_lon, dest_lat]]
        return await self.get_route_with_coords(coords, preference=preference, avoid_features=avoid_features)