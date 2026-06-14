interface AgentTraceProps {
  steps: string[];
}

export default function AgentTrace({ steps }: AgentTraceProps) {
  return (
    <div className="agent-trace">
      {steps.map((step, i) => (
        <div
          key={`${step}-${i}`}
          className={`agent-trace__step ${i === steps.length - 1 ? "agent-trace__step--active" : ""}`}
        >
          <span className="agent-trace__icon">{i < steps.length - 1 ? "✓" : "●"}</span>
          {step}
        </div>
      ))}
    </div>
  );
}
