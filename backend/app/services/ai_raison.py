from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
import httpx

# Elements (scenario facts)
AI_RAISON_ELEMENTS = {
    "fuel_low": "OPT381218",
    "fuel_critical": "OPT381268",
    "urgent": "OPT381318",
    "budget_tight": "OPT381368",
    "route_asked": "OPT381418",
    "road_closure": "OPT381468",
    "leisure_trip and good_weather": "OPT381618",
    "traffic_heavy": "OPT381818",
    "short_city_trip": "OPT381968",
}

# Options (route strategies)
AI_RAISON_OPTIONS = {
    "route_refuel": "OPT381168",
    "route_scenic": "OPT381118",
    "route_detour": "OPT381068",
    "route_toll_free": "OPT381018",
    "route_short": "OPT380968",
    "route_fast": "OPT380918",
}


@dataclass(frozen=True)
class AiRaisonResult:
    solution_labels: List[str]          # ex: ["route_refuel", "route_detour"]
    explanations: Dict[str, List[str]]
    raw: Any


class AiRaisonClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_s: float = 15.0,
    ):
        self.api_key = api_key or os.getenv("AI_RAISON_API_KEY")
        self.base_url = base_url or os.getenv("AI_RAISON_BASE_URL", "https://api.ai-raison.com")
        if not self.api_key:
            raise RuntimeError("AI_RAISON_API_KEY is missing (env var).")
        self.timeout_s = timeout_s

    def _build_payload(self, element_labels: List[str], option_labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        element_labels: list of labels like ["urgent","route_asked","fuel_low"]
        option_labels: list of route option labels
        """
        # default: include all options
        if option_labels is None:
            option_labels = list(AI_RAISON_OPTIONS.keys())

        # build elements
        elements = []
        for lab in element_labels:
            if lab not in AI_RAISON_ELEMENTS:
                raise ValueError(f"Unknown ai-raison element label: {lab}")
            elements.append({
                "parameters": [],
                "label": lab,
                "id": AI_RAISON_ELEMENTS[lab],
            })

        # build options
        options = []
        for lab in option_labels:
            if lab not in AI_RAISON_OPTIONS:
                raise ValueError(f"Unknown ai-raison option label: {lab}")
            options.append({
                "label": lab,
                "id": AI_RAISON_OPTIONS[lab],
            })

        return {"elements": elements, "options": options}

    async def decide(self, element_labels: List[str], option_labels: Optional[List[str]] = None) -> AiRaisonResult:
        """
        Calls: POST https://api.ai-raison.com/executions/<PROJECT_ID>/latest
        with header x-api-key
        """
        project_id = os.getenv("AI_RAISON_PROJECT_ID")
        if not project_id:
            raise RuntimeError("AI_RAISON_PROJECT_ID is missing (env var).")

        url = f"{self.base_url}/executions/{project_id}/latest"

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = self._build_payload(element_labels, option_labels)

        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected ai-raison response (expected list). Got: {type(data)}")

        solutions: List[str] = []
        explanations: Dict[str, List[str]] = {}

        for item in data:
            if item.get("isSolution") is True:
                label = ((item.get("option") or {}).get("label") or "").strip()
                if label:
                    solutions.append(label)
                    explanations[label] = item.get("explanation") or []

        seen = set()
        ordered = []
        for s in solutions:
            if s not in seen:
                seen.add(s)
                ordered.append(s)

        if not ordered:
            ordered = ["route_fast"]

        return AiRaisonResult(solution_labels=ordered, explanations=explanations, raw=data)