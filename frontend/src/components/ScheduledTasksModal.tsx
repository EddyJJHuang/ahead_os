import type { AutonomyTask, NemoClawRuntimeStatus } from "../api/pm_types";

interface ScheduledTasksModalProps {
  tasks: AutonomyTask[];
  pollSeconds: number;
  runtime?: NemoClawRuntimeStatus | null;
  onClose: () => void;
  onRunNow?: (taskId: string) => void;
  runningId?: string | null;
}

const SRC_LABEL: Record<string, string> = {
  jira: "Jira",
  github: "GitHub",
  emails: "Email",
  email: "Email",
  calendar: "Calendar",
  tasks: "Tasks",
  slack: "Slack",
};

function formatCadence(min: number): string {
  if (min < 60) return `every ${min} min`;
  if (min % 1440 === 0) return min === 1440 ? "daily" : `every ${min / 1440} days`;
  if (min % 60 === 0) return min === 60 ? "hourly" : `every ${min / 60} h`;
  return `every ${min} min`;
}

function clock(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? "—"
    : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function ScheduledTasksModal({
  tasks,
  pollSeconds,
  runtime,
  onClose,
  onRunNow,
  runningId,
}: ScheduledTasksModalProps) {
  return (
    <div className="draft-overlay" onClick={onClose}>
      <div
        className="draft-modal tasks-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="draft-modal__header">
          <span className="draft-modal__title">
            Scheduled Tasks · {tasks.length}
          </span>
          <button type="button" className="draft-modal__close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="tasks-modal__sub">
          <span>
            Running on NemoClaw
            {runtime?.name ? ` · ${runtime.name}` : ""}
            {runtime ? (runtime.ok ? " · Ready" : ` · ${runtime.phase}`) : ""}
          </span>
          <span>Scheduler polls every {pollSeconds}s</span>
        </div>

        <div className="tasks-modal__body">
          {tasks.length === 0 && (
            <p className="tasks-modal__empty">
              No recurring tasks yet. Ask PM OS something like “every 30 minutes,
              watch Jira &amp; email for P0s” and launch it from the chat.
            </p>
          )}

          {tasks.map((t) => (
            <div key={t.id} className="task-card">
              <div className="task-card__head">
                <span
                  className={`task-card__type task-card__type--${t.task_type}`}
                >
                  {t.task_type === "creative" ? "Creative" : "Monitor"}
                </span>
                <span className="task-card__title">{t.title}</span>
                <span
                  className={`task-card__state ${t.enabled ? "task-card__state--on" : "task-card__state--off"}`}
                >
                  {t.enabled ? "Active" : "Paused"}
                </span>
              </div>

              <div className="task-card__meta">
                <span>⏱ {formatCadence(t.cadence_minutes)}</span>
                <span>last {clock(t.last_run_at)}</span>
                <span>next {clock(t.next_run_at)}</span>
              </div>

              <div className="task-card__scope">
                {t.source_scope.map((s) => (
                  <span key={s} className="task-card__chip">
                    {SRC_LABEL[s] ?? s}
                  </span>
                ))}
              </div>

              {t.prompt && <p className="task-card__prompt">“{t.prompt}”</p>}

              {t.last_result?.output && (
                <details className="task-card__result">
                  <summary>Latest output</summary>
                  <pre>{t.last_result.output}</pre>
                </details>
              )}
              {t.last_result?.urgent && (
                <span className="task-card__urgent">⚠ Flagged urgent on last run</span>
              )}

              {onRunNow && (
                <div className="task-card__actions">
                  <button
                    type="button"
                    className="btn btn--ghost btn--sm"
                    onClick={() => onRunNow(t.id)}
                    disabled={runningId === t.id}
                  >
                    {runningId === t.id ? "Running…" : "Run now"}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
