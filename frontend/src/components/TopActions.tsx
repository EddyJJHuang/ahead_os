import { useState } from "react";
import { postPmDraft } from "../api/client";
import { DEMO_ARTIFACTS } from "../mock/demoData";
import type {
  ActionItem,
  CompletedAction,
  CompletedActionStatus,
  ExecutionArtifact,
} from "../types";
import { draftToArtifact, enrichAction } from "../utils/actionExecution";
import ExecutionArtifactModal from "./ExecutionArtifactModal";
import Toast from "./Toast";

interface TopActionsProps {
  actions: ActionItem[];
  modelReady: boolean;
}

function statusForArtifact(type: ExecutionArtifact["type"]): CompletedActionStatus {
  switch (type) {
    case "email":
      return "Sent";
    case "meeting":
      return "Scheduled";
    default:
      return "Posted";
  }
}

function toastForArtifact(type: ExecutionArtifact["type"]): string {
  switch (type) {
    case "email":
      return "Email sent (simulated)";
    case "meeting":
      return "Meeting scheduled (simulated)";
    default:
      return "Review request posted (simulated)";
  }
}

export default function TopActions({ actions, modelReady }: TopActionsProps) {
  const [artifact, setArtifact] = useState<ExecutionArtifact | null>(null);
  const [pendingAction, setPendingAction] = useState<ActionItem | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [completed, setCompleted] = useState<CompletedAction[]>([]);

  const completedIds = new Set(completed.map((item) => item.id));
  const activeActions = actions.filter((action) => !completedIds.has(action.id));

  const handleCta = async (action: ActionItem) => {
    setLoadingId(action.id);

    const enriched = { ...action, ...enrichAction(action) };
    let result: ExecutionArtifact | null = null;

    if (modelReady && enriched.draft_kind && enriched.context) {
      const res = await postPmDraft({
        kind: enriched.draft_kind,
        context: enriched.context,
      });
      if (res?.draft) {
        result = draftToArtifact(enriched, res.draft);
      }
    }

    if (!result) {
      result =
        DEMO_ARTIFACTS[action.id] ??
        draftToArtifact(
          enriched,
          enriched.rationale ?? `Generated content for ${action.title}.`
        );
    }

    await new Promise((r) => setTimeout(r, 300));
    setPendingAction(action);
    setArtifact(result);
    setLoadingId(null);
  };

  const handlePrimary = () => {
    if (!artifact || !pendingAction) return;

    const status = statusForArtifact(artifact.type);
    setCompleted((prev) => {
      if (prev.some((item) => item.id === pendingAction.id)) return prev;
      return [...prev, { id: pendingAction.id, title: pendingAction.title, status }];
    });
    setArtifact(null);
    setPendingAction(null);
    setToast(toastForArtifact(artifact.type));
  };

  const handleCloseModal = () => {
    setArtifact(null);
    setPendingAction(null);
  };

  return (
    <>
      <div className="actions-panel">
        <div className="actions-list">
          {activeActions.map((action) => {
            const meta = enrichAction(action);
            const explanation = meta.explanation || action.rationale || "";
            const ctaLabel = meta.ctaLabel || "Generate";

            return (
              <div key={action.id} className="action-card action-card--execution">
                <div className="action-card__title">{action.title}</div>
                <p className="action-card__explanation">{explanation}</p>
                <button
                  type="button"
                  className="btn btn--primary btn--sm action-card__cta"
                  onClick={() => handleCta(action)}
                  disabled={loadingId === action.id}
                >
                  {loadingId === action.id ? "Generating…" : ctaLabel}
                </button>
              </div>
            );
          })}
        </div>

        {completed.length > 0 && (
          <>
            <div className="actions-divider" role="separator" />
            <div className="actions-completed">
              <div className="actions-completed__heading">Completed</div>
              <ul className="actions-completed__list">
                {completed.map((item) => (
                  <li key={item.id} className="action-completed">
                    <span className="action-completed__check" aria-hidden>
                      ✓
                    </span>
                    <span className="action-completed__title">{item.title}</span>
                    <span className="action-completed__status">— {item.status}</span>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>

      {artifact && (
        <ExecutionArtifactModal
          artifact={artifact}
          onClose={handleCloseModal}
          onPrimary={handlePrimary}
        />
      )}

      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
    </>
  );
}
