import { useEffect, useState } from "react";

interface TraceLoaderProps {
  steps: string[];
  active: boolean;
}

export default function TraceLoader({ steps, active }: TraceLoaderProps) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (!active) {
      setCurrentStep(0);
      return;
    }

    setCurrentStep(0);
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= steps.length - 1) {
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 600);

    return () => clearInterval(interval);
  }, [active, steps]);

  if (!active) return null;

  return (
    <div className="trace-loader">
      {steps.map((step, i) => {
        const isDone = i < currentStep;
        const isActive = i === currentStep;
        return (
          <div
            key={step}
            className={`trace-step ${isActive ? "trace-step--active" : ""} ${isDone ? "trace-step--done" : ""}`}
          >
            <span className="trace-step__icon">
              {isDone ? "✓" : isActive ? "●" : "○"}
            </span>
            {step}
          </div>
        );
      })}
    </div>
  );
}
