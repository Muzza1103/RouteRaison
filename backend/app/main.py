from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
import math
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from services.weather import WeatherService
from services.ai_raison import AiRaisonClient
from services.routing_ors import ORSRoutingService
from services.poi_fuel import FuelStationService  # ton fichier stations essence
from services.traffic_tomtom import TomTomTrafficService

load_dotenv()

app = FastAPI(title="RouteRaison Backend", version="0.2.0")

traffic_service = TomTomTrafficService()
weather_service = WeatherService()
ai_raison_client = AiRaisonClient()
ors_service = ORSRoutingService()
fuel_service = FuelStationService()

LONG_TRIP_KM = float(os.getenv("LONG_TRIP_KM", "60"))
CITY_TRIP_KM = float(os.getenv("CITY_TRIP_KM", "10"))


class Point(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class PlanRequest(BaseModel):
    origin: Point
    destination: Point

    urgent: bool = False
    budget_tight: bool = False
    kids_onboard: bool = False
    fatigue: bool = False
    leisure_trip: bool = False
    fuel_low: bool = False

    fuel_critical: bool = False
    road_closure: bool = False
    traffic_heavy: bool = False
    good_weather: Optional[bool] = None
    short_city_trip: Optional[bool] = None

    forced_option: Optional[str] = None


class ContextResponse(BaseModel):
    scenarios: List[str]
    debug: Dict[str, Any] = None


class PlanResponse(BaseModel):
    chosen_solutions: List[str]
    scenarios: List[str]
    ai_raison_elements: List[str]
    route: Dict[str, Any]
    ai_raison_raw: Any
    ai_raison_explanations: Dict[str, List[str]] = None


def is_night_now() -> bool:
    hour = datetime.now().hour
    return hour >= 21 or hour < 6


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def apply_implications(elements: List[str]) -> List[str]:
    s = set(elements)
    if "fuel_critical" in s:
        s.add("fuel_low")
    if "road_closure" in s:
        s.add("traffic_heavy")
    return sorted(s)


def build_ai_raison_elements_from_scenarios(scenarios: List[str]) -> List[str]:
    """
    Convert backend scenarios into ai-raison 'elements' labels.
    """
    s = set(scenarios)
    elements: List[str] = []

    # Always include route_asked
    elements.append("route_asked")

    for lab in [
        "fuel_low",
        "fuel_critical",
        "urgent",
        "budget_tight",
        "road_closure",
        "traffic_heavy",
        "short_city_trip",
    ]:
        if lab in s:
            elements.append(lab)

    # composite label
    if "leisure_trip" in s and "good_weather" in s:
        elements.append("leisure_trip and good_weather")

    return apply_implications(elements)


def extract_solutions_and_explanations(ai_raw: Any) -> (List[str], Dict[str, List[str]]):
    if not isinstance(ai_raw, list):
        return ["route_fast"], {}

    sols: List[str] = []
    exps: Dict[str, List[str]] = {}
    for item in ai_raw:
        if item.get("isSolution") is True:
            label = ((item.get("option") or {}).get("label") or "").strip()
            if label:
                sols.append(label)
                exps[label] = item.get("explanation") or []

    seen = set()
    out = []
    for x in sols:
        if x not in seen:
            seen.add(x)
            out.append(x)

    if not out:
        out = ["route_fast"]
    return out, exps


def compile_ors_plan(solution_labels: List[str]) -> Dict[str, Any]:
    """
    Combine multiple ai-raison solutions into an ORS request plan:
      - need_refuel into add waypoint station
      - avoid_features into list (highways, tollways)
      - preference into fastest/shortest
    """
    s = set(solution_labels)

    avoid: List[str] = []
    # constraints
    if "route_detour" in s:
        avoid.append("highways")
    if "route_toll_free" in s:
        avoid.append("tollways")
    if "route_scenic" in s:
        avoid.append("highways")

    # objective preference
    preference = "fastest"
    if "route_short" in s or "route_scenic" in s:
        preference = "shortest"
    if "route_fast" in s:
        preference = "fastest"

    return {
        "need_refuel": "route_refuel" in s,
        "avoid_features": sorted(set(avoid)),
        "preference": preference,
    }


async def build_scenarios(req: PlanRequest) -> ContextResponse:
    scenarios: List[str] = []
    debug: Dict[str, Any] = {}

    #weather scenarios
    try:
        wctx = await weather_service.get_scenarios(req.origin.lat, req.origin.lon)
        scenarios.extend(wctx.scenarios)
        debug["weather_main"] = wctx.raw_main
        debug["weather_scenarios"] = wctx.scenarios
    except Exception as e:
        debug["weather_error"] = str(e)

    #time
    if is_night_now():
        scenarios.append("night")
    else:
        scenarios.append("day")

    #good_weather heuristic (for scenic)
    if not any(x in scenarios for x in ["rain", "snow", "fog", "storm"]):
        scenarios.append("good_weather")

    # override only if we force choices on the frontend
    if req.good_weather is True and "good_weather" not in scenarios:
        scenarios.append("good_weather")

    #trip length
    approx_km = haversine_km(req.origin.lat, req.origin.lon, req.destination.lat, req.destination.lon)
    debug["approx_distance_km"] = approx_km
    if approx_km >= LONG_TRIP_KM:
        scenarios.append("long_trip")
    if approx_km <= CITY_TRIP_KM:
        scenarios.append("short_city_trip")

    #user flags
    if req.urgent:
        scenarios.append("urgent")
    if req.budget_tight:
        scenarios.append("budget_tight")
    if req.kids_onboard:
        scenarios.append("kids_onboard")
    if req.fatigue:
        scenarios.append("fatigue")
    if req.leisure_trip:
        scenarios.append("leisure_trip")
    if req.fuel_low:
        scenarios.append("fuel_low")

    # extra inputs (optional)
    if req.fuel_critical:
        scenarios.append("fuel_critical")
    if req.road_closure:
        scenarios.append("road_closure")
    if req.traffic_heavy:
        scenarios.append("traffic_heavy")

    # allow forcing short_city_trip
    if req.short_city_trip is True and "short_city_trip" not in scenarios:
        scenarios.append("short_city_trip")

    if not req.road_closure and not req.traffic_heavy:
        try:
            margin = float(os.getenv("TOMTOM_BBOX_MARGIN_DEG", "0.02"))

            min_lat = req.origin.lat - margin
            max_lat = req.origin.lat + margin
            min_lon = req.origin.lon - margin
            max_lon = req.origin.lon + margin

            tt = await traffic_service.incidents_bbox(
                min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon
            )

            scenarios.extend(tt.scenarios)
            debug["tomtom_bbox"] = {"min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon}
            debug["tomtom_scenarios"] = tt.scenarios
            debug["tomtom_error"] = tt.error
            debug["tomtom_endpoint"] = tt.endpoint

        except Exception as e:
            debug["tomtom_error"] = str(e)
    else:
        debug["tomtom_skipped"] = True

    # dedup preserve order
    seen = set()
    scenarios_unique: List[str] = []
    for s in scenarios:
        if s not in seen:
            seen.add(s)
            scenarios_unique.append(s)

    return ContextResponse(scenarios=scenarios_unique, debug=debug)


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/context", response_model=ContextResponse)
async def context(req: PlanRequest):
    return await build_scenarios(req)


@app.post("/plan", response_model=PlanResponse)
async def plan(req: PlanRequest):
    # scenarios
    ctx = await build_scenarios(req)
    scenarios = ctx.scenarios

    if "fuel_critical" in scenarios and "fuel_low" not in scenarios:
        scenarios.append("fuel_low")
    if "road_closure" in scenarios and "traffic_heavy" not in scenarios:
        scenarios.append("traffic_heavy")

    ai_elements: List[str] = []

    # ai-raison decision(s)
    if req.forced_option:
        solution_labels = [req.forced_option]
        ai_raw: Any = {"forced": True}
        explanations: Dict[str, List[str]] = {}
        ai_elements = ["forced_option"]
    else:
        try:
            ai_elements = build_ai_raison_elements_from_scenarios(scenarios)
            decision = await ai_raison_client.decide(ai_elements)
            ai_raw = getattr(decision, "raw", decision)
            solution_labels, explanations = extract_solutions_and_explanations(ai_raw)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"ai-raison error: {e}")

    print("AI-RAISON elements sent:", ai_elements)

    # compile ORS plan from multiple solutions
    plan_cfg = compile_ors_plan(solution_labels)

    # build coords (with refuel waypoint if needed)
    coords = [[req.origin.lon, req.origin.lat], [req.destination.lon, req.destination.lat]]
    station_used = None

    if plan_cfg["need_refuel"]:
        stations, fuel_dbg = await fuel_service.find_nearby(req.origin.lat, req.origin.lon, radius_m=4000, limit=5)
        print("FUEL SEARCH DEBUG:", fuel_dbg)

        if stations:
            st = stations[0]
            station_used = {"name": st.name, "lat": st.lat, "lon": st.lon}
            coords = [
                [req.origin.lon, req.origin.lat],
                [st.lon, st.lat],
                [req.destination.lon, req.destination.lat],
            ]
            print("REFUEL: using station:", station_used)
        else:
            # fallback: route without station
            station_used = None
            print("REFUEL: no station found -> fallback to direct route")

    # ORS route
    try:
        route = await ors_service.get_route_with_coords(
            coords,
            preference=plan_cfg["preference"],
            avoid_features=plan_cfg["avoid_features"],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ORS routing error: {e}")

    route_payload = {
        "distance_m": route.distance_m,
        "duration_s": route.duration_s,
        "geometry": route.geometry,
        "debug_plan": plan_cfg,
        "debug_station": station_used,
    }

    return PlanResponse(
        chosen_solutions=solution_labels,
        scenarios=scenarios,
        ai_raison_elements=ai_elements,
        route=route_payload,
        ai_raison_raw=ai_raw,
        ai_raison_explanations=explanations,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)