import type { ContextResponse, PlanRequest, PlanResponse } from "../types/routeraison";
import { getJSON, postJSON } from "./client";

export function health() {
  return getJSON<{ ok: boolean }>("/health");
}

export function fetchContext(req: PlanRequest) {
  return postJSON<ContextResponse>("/context", req);
}

export function planRoute(req: PlanRequest) {
  return postJSON<PlanResponse>("/plan", req);
}