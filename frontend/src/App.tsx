import { useMemo, useState } from "react";
import "./App.css";

import type {
  ContextResponse,
  DecisionMode,
  LatLon,
  PlanRequest,
  PlanResponse,
  RouteOption,
} from "./types/routeraison";
import { planRoute, fetchContext } from "./api/routeraison";
import { ControlPanel } from "./components/Controls/ControlPanel";
import { DebugPanel } from "./components/Controls/DebugPanel";
import { MapView } from "./components/Map/MapView";

function emptyReq(origin?: LatLon, destination?: LatLon): PlanRequest {
  return {
    origin: origin ?? { lat: 48.8566, lon: 2.3522 },
    destination: destination ?? { lat: 48.8584, lon: 2.2945 },
    urgent: false,
    budget_tight: false,
    kids_onboard: false,
    fatigue: false,
    leisure_trip: false,
    fuel_low: false,
    fuel_critical: false,
    road_closure: false,
    traffic_heavy: false,
    short_city_trip: null,
    forced_option: null,
  };
}

export default function App() {
  const [mode, setMode] = useState<DecisionMode>("ARGUED");

  const [picking, setPicking] = useState<"ORIGIN" | "DESTINATION">("ORIGIN");
  const [origin, setOrigin] = useState<LatLon | undefined>(undefined);
  const [destination, setDestination] = useState<LatLon | undefined>(undefined);

  const [req, setReq] = useState<PlanRequest>(() => emptyReq());
  const [forcedOption, setForcedOption] = useState<RouteOption | "">("");

  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [context, setContext] = useState<ContextResponse | null>(null);

  const [loadingPlan, setLoadingPlan] = useState(false);
  const [loadingContext, setLoadingContext] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function changeMode(nextMode: DecisionMode) {
    setMode(nextMode);

    // Si on quitte "Scénarios forcés", on reset les flags forcés
    if (nextMode !== "FORCED_SCENARIOS") {
      setReq((r) => {
        const next: any = { ...r, traffic_heavy: false, road_closure: false };
        // good_weather doit être ABSENT si pas forcé => backend décide
        delete next.good_weather;
        return next;
      });
    }

    // Si on quitte "Option forcée", on reset la sélection
    if (nextMode !== "FORCED_OPTION") {
      setForcedOption("");
    }
  }

  const effectiveReq: PlanRequest = useMemo(() => {
    const o = origin ?? req.origin;
    const d = destination ?? req.destination;

    // forced option mode -> send forced_option
    const forced_option =
      mode === "FORCED_OPTION" && forcedOption ? forcedOption : null;

    return {
      ...req,
      origin: o,
      destination: d,
      forced_option,
    };
  }, [req, origin, destination, mode, forcedOption]);

  function onPick(which: "ORIGIN" | "DESTINATION", lat: number, lon: number) {
    if (which === "ORIGIN") setOrigin({ lat, lon });
    else setDestination({ lat, lon });
  }

  async function onPlan() {
    setError(null);
    setPlan(null);

    const o = effectiveReq.origin;
    const d = effectiveReq.destination;
    if (!o || !d) {
      setError("Choisis un départ et une arrivée.");
      return;
    }

    if (mode === "FORCED_OPTION" && !forcedOption) {
      setError("Choisis une option forcée.");
      return;
    }

    setLoadingPlan(true);
    try {
      const data = await planRoute(effectiveReq);
      setPlan(data);
    } catch (e: any) {
      setError(e?.message ?? "Erreur /plan");
    } finally {
      setLoadingPlan(false);
    }
  }

  async function onFetchContext() {
    setError(null);
    setContext(null);

    setLoadingContext(true);
    try {
      const data = await fetchContext(effectiveReq);
      setContext(data);
    } catch (e: any) {
      setError(e?.message ?? "Erreur /context");
    } finally {
      setLoadingContext(false);
    }
  }

  return (
    <div className="app">
      <div className="left">
        <ControlPanel
          mode={mode}
          setMode={changeMode}
          picking={picking}
          setPicking={setPicking}
          origin={origin ?? effectiveReq.origin}
          destination={destination ?? effectiveReq.destination}
          setOrigin={(p) => setOrigin(p)}
          setDestination={(p) => setDestination(p)}
          req={req}
          setReq={setReq}
          forcedOption={forcedOption}
          setForcedOption={setForcedOption}
          onPlan={onPlan}
          onFetchContext={onFetchContext}
          loadingPlan={loadingPlan}
          loadingContext={loadingContext}
          error={error}
        />

        <DebugPanel plan={plan} context={context} />
      </div>

      <div className="right">
        <MapView
          origin={origin ?? effectiveReq.origin}
          destination={destination ?? effectiveReq.destination}
          picking={picking}
          onPick={onPick}
          plan={plan}
        />
      </div>
    </div>
  );
}