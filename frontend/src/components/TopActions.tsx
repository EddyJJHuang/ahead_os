import { useState } from "react";
import type { ActionItem, DraftContent } from "../types";
import { DEMO_DRAFTS } from "../mock/demoData";
import DraftModal from "./DraftModal";

interface TopActionsProps {
  actions: ActionItem[];
}

export default function TopActions({ actions }: TopActionsProps) {
  const [draft, setDraft] = useState<DraftContent | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleDraft = async (action: ActionItem) => {
    setLoadingId(action.id);
    // TODO: POST /api/draft
    await new Promise((r) => setTimeout(r, 350));
    setDraft(
      DEMO_DRAFTS[action.id] ?? {
        action_id: action.id,
        action_title: action.title,
        subject: `Draft: ${action.title}`,
        body: `Draft for "${action.title}".\n\n— PM`,
      }
    );
    setLoadingId(null);
  };

  return (
    <>
      <div className="actions-list">
        {actions.map((action) => (
          <div key={action.id} className="action-card">
            <div className="action-card__title">{action.title}</div>
            <div className="action-card__meta">
              <div className="meta-tag">
                <span className="meta-tag__label">Impact</span>
                <span
                  className={`meta-tag__value meta-tag__value--${action.impact.toLowerCase()}`}
                >
                  {action.impact}
                </span>
              </div>
              <div className="meta-tag">
                <span className="meta-tag__label">Effort</span>
                <span className="meta-tag__value">{action.effort}</span>
              </div>
            </div>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={() => handleDraft(action)}
              disabled={loadingId === action.id}
            >
              {loadingId === action.id ? "Generating…" : "Generate draft"}
            </button>
          </div>
        ))}
      </div>
      {draft && <DraftModal draft={draft} onClose={() => setDraft(null)} />}
    </>
  );
}
