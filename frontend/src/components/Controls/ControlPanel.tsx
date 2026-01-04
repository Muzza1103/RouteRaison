import type { Dispatch, SetStateAction } from "react";
import type { DecisionMode, LatLon, PlanRequest, RouteOption } from "../../types/routeraison";
import { AddressSearch } from "./AddressSearch";

const OPTIONS: RouteOption[] = [
  "route_fast",
  "route_short",
  "route_scenic",
  "route_refuel",
  "route_detour",
  "route_toll_free",
];

// Mode “Décision argumentée”
const BASE_FLAGS: Array<{ key: keyof PlanRequest; label: string }> = [
  { key: "urgent", label: "urgent" },
  { key: "fuel_low", label: "fuel_low" },
  { key: "fuel_critical", label: "fuel_critical" },
  { key: "budget_tight", label: "budget_tight" },
  { key: "leisure_trip", label: "leisure_trip" },
];

// Mode “Scénarios forcés” = base + extras
const FORCED_EXTRA_FLAGS: Array<{ key: keyof PlanRequest; label: string }> = [
  { key: "traffic_heavy", label: "traffic_heavy" },
  { key: "road_closure", label: "road_closure" },
  { key: "good_weather", label: "good_weather (forcer)" }, // force-only
];

export function ControlPanel(props: {
  mode: DecisionMode;
  setMode: (m: DecisionMode) => void;

  picking: "ORIGIN" | "DESTINATION";
  setPicking: (p: "ORIGIN" | "DESTINATION") => void;

  origin?: LatLon;
  destination?: LatLon;
  setOrigin: (p: LatLon) => void;
  setDestination: (p: LatLon) => void;

  req: PlanRequest;
  setReq: Dispatch<SetStateAction<PlanRequest>>;

  forcedOption: RouteOption | "";
  setForcedOption: (o: RouteOption | "") => void;

  onPlan: () => void;
  onFetchContext: () => void;

  loadingPlan: boolean;
  loadingContext: boolean;
  error?: string | null;
}) {
  const r = props.req;

  function setFlag<K extends keyof PlanRequest>(k: K, v: PlanRequest[K]) {
    props.setReq((prev) => ({ ...prev, [k]: v }));
  }

  //good_weather : si décoché -> undefined => non envoyé => backend décide
  function setGoodWeatherForced(checked: boolean) {
    props.setReq((prev) => ({
      ...prev,
      good_weather: checked ? true : undefined,
    }));
  }

  const flagsToShow =
    props.mode === "FORCED_SCENARIOS"
      ? [...BASE_FLAGS, ...FORCED_EXTRA_FLAGS]
      : BASE_FLAGS;

  return (
    <div className="panel">
      <h1>RouteRaison</h1>

      <div className="block">
        <div className="label">Mode</div>

        <label className="radio">
          <input
            type="radio"
            checked={props.mode === "ARGUED"}
            onChange={() => props.setMode("ARGUED")}
          />
          Décision argumentée (ai-raison)
        </label>

        <label className="radio">
          <input
            type="radio"
            checked={props.mode === "FORCED_SCENARIOS"}
            onChange={() => props.setMode("FORCED_SCENARIOS")}
          />
          Scénarios forcés (ai-raison sur faits imposés)
        </label>

        <label className="radio">
          <input
            type="radio"
            checked={props.mode === "FORCED_OPTION"}
            onChange={() => props.setMode("FORCED_OPTION")}
          />
          Option forcée (sans ai-raison)
        </label>
      </div>

      <div className="block">
        <div className="label">Départ / Arrivée</div>

        <AddressSearch
          label="Départ (adresse)"
          placeholder="Ex: 6 rue Claude Monet, 95140"
          onSelect={(p) => props.setOrigin(p)}
        />
        <AddressSearch
          label="Arrivée (adresse)"
          placeholder="Ex: Tour Eiffel"
          onSelect={(p) => props.setDestination(p)}
        />

        <div className="row">
          <button
            className={props.picking === "ORIGIN" ? "active" : ""}
            onClick={() => props.setPicking("ORIGIN")}
          >
            Placer Départ (clic carte)
          </button>
          <button
            className={props.picking === "DESTINATION" ? "active" : ""}
            onClick={() => props.setPicking("DESTINATION")}
          >
            Placer Arrivée (clic carte)
          </button>
        </div>

        <div className="coords">
          <div>
            <b>Origin:</b>{" "}
            {props.origin ? `${props.origin.lat.toFixed(5)}, ${props.origin.lon.toFixed(5)}` : "—"}
          </div>
          <div>
            <b>Destination:</b>{" "}
            {props.destination
              ? `${props.destination.lat.toFixed(5)}, ${props.destination.lon.toFixed(5)}`
              : "—"}
          </div>
        </div>
      </div>

      {/* FLAGS */}
      {props.mode !== "FORCED_OPTION" && (
        <div className="block">
          <div className="label">
            {props.mode === "ARGUED" ? "Scénarios (base)" : "Scénarios (forcés)"}
          </div>

          <div className="grid">
            {flagsToShow.map(({ key, label }) => {
              const isGoodWeather = key === "good_weather";
              const checked = isGoodWeather ? r.good_weather === true : !!(r as any)[key];

              return (
                <label key={String(key)}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => {
                      const c = e.target.checked;
                      if (isGoodWeather) setGoodWeatherForced(c);
                      else setFlag(key, c as any);
                    }}
                  />
                  {label}
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* FORCED OPTION */}
      {props.mode === "FORCED_OPTION" && (
        <div className="block">
          <div className="label">Option forcée</div>
          <select
            value={props.forcedOption}
            onChange={(e) => props.setForcedOption(e.target.value as any)}
          >
            <option value="">— choisir —</option>
            {OPTIONS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
          <div className="hint">
            Avec <code>forced_option</code>, ai-raison est bypass.
          </div>
        </div>
      )}

      <div className="block">
        <button className="primary" onClick={props.onPlan} disabled={props.loadingPlan}>
          {props.loadingPlan ? "Calcul…" : "Calculer /plan"}
        </button>

        <button onClick={props.onFetchContext} disabled={props.loadingContext}>
          {props.loadingContext ? "…" : "Voir /context (debug)"}
        </button>

        {props.error && <div className="error">{props.error}</div>}
      </div>
    </div>
  );
}