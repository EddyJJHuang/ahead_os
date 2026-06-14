import type { ExecutiveDecisionData } from "../types";
import { LOADING_TRACE } from "../mock/demoData";
import TraceLoader from "./TraceLoader";

interface ExecutiveDecisionProps {
  data: ExecutiveDecisionData | null;
  loading: boolean;
  usingMock?: boolean;
}

export default function ExecutiveDecision({
  data,
  loading,
  usingMock,
}: ExecutiveDecisionProps) {
  if (loading || !data) {
    return <TraceLoader steps={LOADING_TRACE} active={loading} />;
  }

  return (
    <div className="executive">
      {usingMock && (
        <span className="panel-badge panel-badge--demo">Demo data</span>
      )}

      <h2 className="executive__headline">{data.headline}</h2>

      <div className="executive__verdict">
        <div className="verdict-row">
          <span className="verdict-row__label">Ship Readiness</span>
          <span
            className={`verdict-row__value ${data.ship_readiness === "NO" ? "verdict-row__value--no" : ""}`}
          >
            {data.ship_readiness}
          </span>
        </div>

        <div className="verdict-row">
          <span className="verdict-row__label">Recommendation</span>
          <span className="verdict-row__value">{data.recommendation}</span>
        </div>

        <div className="verdict-row">
          <span className="verdict-row__label">Risk Level</span>
          <span
            className={`verdict-row__value ${data.risk_level === "Critical" ? "verdict-row__value--critical" : ""}`}
          >
            {data.risk_level}
          </span>
        </div>
      </div>

      <p className="executive__summary">{data.summary}</p>

      <div className="evidence-strength">
        <span className="evidence-strength__label">Evidence strength</span>
        <span className="evidence-strength__value">
          {data.evidence_strength}
        </span>
        <span className="evidence-strength__sources">
          Based on {data.evidence_sources.join(" + ")}
        </span>
      </div>
    </div>
  );
}
