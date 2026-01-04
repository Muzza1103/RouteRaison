from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import os
import httpx


@dataclass(frozen=True)
class WeatherContext:
    scenarios: List[str]
    raw_main: Optional[str] = None  # ex: "Rain", "Clear" pour debug


class WeatherService:
    """
    Uses OpenWeather 'Current Weather' endpoint.
    Converts weather conditions into logical scenarios used by ai-raison.
    """

    def __init__(self, api_key: Optional[str] = None, timeout_s: float = 10.0):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENWEATHER_API_KEY is missing (env var).")
        self.timeout_s = timeout_s

    async def get_scenarios(self, lat: float, lon: float) -> WeatherContext:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": self.api_key}

        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        scenarios: List[str] = []
        # OpenWeather returns a list in "weather"
        main = None
        if isinstance(data.get("weather"), list) and data["weather"]:
            main = (data["weather"][0].get("main") or "").strip()

        main_lower = (main or "").lower()
        if "rain" in main_lower or "drizzle" in main_lower:
            scenarios.append("rain")
        if "snow" in main_lower:
            scenarios.append("snow")
        if "fog" in main_lower or "mist" in main_lower or "haze" in main_lower:
            scenarios.append("fog")
        if "thunderstorm" in main_lower:
            scenarios.append("storm")

        return WeatherContext(scenarios=scenarios, raw_main=main)