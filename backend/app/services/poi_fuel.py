from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import httpx


@dataclass(frozen=True)
class FuelStation:
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class FuelSearchDebug:
    ok: bool
    endpoint_used: Optional[str]
    error: Optional[str]
    count: int


class FuelStationService:
    """
    Uses Overpass API (OpenStreetMap) to find fuel stations near a point.
    Free but rate-limited and sometimes overloaded => must fail gracefully.
    """

    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.nchc.org.tw/api/interpreter",
    ]

    def __init__(self, overpass_url: Optional[str] = None, timeout_s: float = 35.0, query_timeout_s: int = 60):
        # If a custom URL is provided, try it first, then fallback to public endpoints
        self.overpass_url = overpass_url
        self.timeout_s = timeout_s
        self.query_timeout_s = query_timeout_s

    def _build_query(self, lat: float, lon: float, radius_m: int, limit: int) -> str:
        return f"""
        [out:json][timeout:{self.query_timeout_s}];
        (
        node["amenity"="fuel"](around:{radius_m},{lat},{lon});
        way["amenity"="fuel"](around:{radius_m},{lat},{lon});
        relation["amenity"="fuel"](around:{radius_m},{lat},{lon});
        );
        out center {limit};
        """

    def _parse(self, data: dict, limit: int) -> List[FuelStation]:
        stations: List[FuelStation] = []
        for el in data.get("elements", []):
            el_lat = el.get("lat") or (el.get("center") or {}).get("lat")
            el_lon = el.get("lon") or (el.get("center") or {}).get("lon")
            if el_lat is None or el_lon is None:
                continue

            tags = el.get("tags") or {}
            name = tags.get("name") or "Fuel station"
            stations.append(FuelStation(name=name, lat=float(el_lat), lon=float(el_lon)))

        return stations[:limit]

    async def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_m: int = 2000,
        limit: int = 5
    ) -> Tuple[List[FuelStation], FuelSearchDebug]:
        """
        Returns (stations, debug).
        """
        query = self._build_query(lat, lon, radius_m, limit)

        endpoints: List[str] = []
        if self.overpass_url:
            endpoints.append(self.overpass_url)
        endpoints.extend(self.OVERPASS_ENDPOINTS)

        last_err: Optional[str] = None

        for endpoint in endpoints:
            try:
                async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                    r = await client.post(endpoint, data=query)
                    r.raise_for_status()
                    data = r.json()

                stations = self._parse(data, limit)
                dbg = FuelSearchDebug(
                    ok=True,
                    endpoint_used=endpoint,
                    error=None,
                    count=len(stations),
                )
                return stations, dbg

            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
                last_err = f"{type(e).__name__}: {e}"
                continue

        # All endpoints failed
        return [], FuelSearchDebug(ok=False, endpoint_used=None, error=last_err, count=0)