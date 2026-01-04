from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional
import os
import httpx


@dataclass(frozen=True)
class TomTomTrafficResult:
    scenarios: List[str]
    raw: Any
    error: Optional[str] = None
    endpoint: Optional[str] = None


class TomTomTrafficService:
    def __init__(self, api_key: Optional[str] = None, timeout_s: float = 12.0):
        self.api_key = api_key or os.getenv("TOMTOM_API_KEY")
        if not self.api_key:
            raise RuntimeError("TOMTOM_API_KEY is missing (env var).")
        self.timeout_s = timeout_s
        self.base_url = "https://api.tomtom.com"

    async def incidents_bbox(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float
    ) -> TomTomTrafficResult:
        url = f"{self.base_url}/traffic/services/5/incidentDetails"

        #west,south,east,north (lon,lat,lon,lat)
        bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"

        fields = "{incidents{type,geometry{type,coordinates},properties{iconCategory,magnitudeOfDelay,roadNumbers,events{description}}}}"

        params = {
            "key": self.api_key,
            "bbox": bbox,
            "fields": fields,
            "language": "en-GB",
            "timeValidityFilter": "present",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            return TomTomTrafficResult(
                scenarios=[],
                raw=None,
                error=f"{type(e).__name__}: {e}",
                endpoint=str(r.url) if "r" in locals() else url,
            )

        scenarios: List[str] = []
        incidents = (data.get("incidents") or [])

        if incidents:
            #any incident in bbox => traffic_heavy
            scenarios.append("traffic_heavy")

            # Detect closures from descriptions
            for inc in incidents:
                props = inc.get("properties") or {}
                events = props.get("events") or []
                for ev in events:
                    desc = (ev.get("description") or "").lower()
                    if "closed" in desc or "closure" in desc or "road closed" in desc:
                        scenarios.append("road_closure")
                        break
                if "road_closure" in scenarios:
                    break

        out: List[str] = []
        seen = set()
        for s in scenarios:
            if s not in seen:
                seen.add(s)
                out.append(s)

        return TomTomTrafficResult(
            scenarios=out,
            raw=data,
            error=None,
            endpoint=str(r.url),
        )