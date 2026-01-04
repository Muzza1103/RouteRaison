import type { Geometry } from "geojson";

export type LatLon = { lat: number; lon: number };

export type DecisionMode = "ARGUED" | "FORCED_SCENARIOS" | "FORCED_OPTION";

export type RouteOption =
  | "route_fast"
  | "route_short"
  | "route_scenic"
  | "route_refuel"
  | "route_detour"
  | "route_toll_free";

export type PlanRequest = {
  origin: LatLon;
  destination: LatLon;

  urgent?: boolean;
  budget_tight?: boolean;
  kids_onboard?: boolean;
  fatigue?: boolean;
  leisure_trip?: boolean;
  fuel_low?: boolean;

  fuel_critical?: boolean;
  road_closure?: boolean;
  traffic_heavy?: boolean;

  good_weather?: boolean;

  short_city_trip?: boolean | null;

  forced_option?: RouteOption | null;
};

export type ContextResponse = {
  scenarios: string[];
  debug?: Record<string, any> | null;
};

export type PlanResponse = {
  chosen_solutions: string[];
  scenarios: string[];
  ai_raison_elements: string[];
  route: {
    distance_m: number;
    duration_s: number;
    geometry: Geometry;
    debug_plan: {
      need_refuel: boolean;
      avoid_features: string[];
      preference: string;
    };
    debug_station?: { name: string; lat: number; lon: number } | null;
  };
  ai_raison_raw: any;
  ai_raison_explanations?: Record<string, string[]> | null;
};
