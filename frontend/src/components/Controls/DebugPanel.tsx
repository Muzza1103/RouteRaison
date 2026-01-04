import type { ContextResponse, PlanResponse } from "../../types/routeraison";
import { formatDuration, formatKm } from "../../utils/format";

export function DebugPanel(props: {
  plan?: PlanResponse | null;
  context?: ContextResponse | null;
}) {
  const plan = props.plan;
  const ctx = props.context;

  return (
    <div className="debug">
      <div className="label">Debug</div>

      <div className="debugBlock">
        <div className="sub">Décision</div>
        <pre>
          {JSON.stringify(
            {
              chosen_solutions: plan?.chosen_solutions ?? null,
              ai_raison_elements: plan?.ai_raison_elements ?? null,
              ai_raison_explanations: plan?.ai_raison_explanations ?? null,
            },
            null,
            2
          )}
        </pre>
      </div>

      <div className="debugBlock">
        <div className="sub">Scénarios</div>
        <pre>{JSON.stringify(plan?.scenarios ?? null, null, 2)}</pre>
      </div>

      <div className="debugBlock">
        <div className="sub">Route</div>
        <pre>
          {JSON.stringify(
            plan
              ? {
                  distance: formatKm(plan.route.distance_m),
                  duration: formatDuration(plan.route.duration_s),
                  debug_plan: plan.route.debug_plan,
                  debug_station: plan.route.debug_station ?? null,
                }
              : null,
            null,
            2
          )}
        </pre>
      </div>

      <div className="debugBlock">
        <div className="sub">/context (enrichissement)</div>
        <pre>{JSON.stringify(ctx ?? null, null, 2)}</pre>
      </div>
    </div>
  );
}