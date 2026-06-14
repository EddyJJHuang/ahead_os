import { useState } from "react";
import { postDraft } from "../api/client";
import type { ActionItem, DraftContent } from "../types";
import { DEMO_DRAFTS } from "../mock/demoData";
import DraftModal from "./DraftModal";

interface TopActionsProps {
  actions: ActionItem[];
}

/** Split an LLM draft into a subject line + body (emails start with "Subject:"). */
function toDraftContent(action: ActionItem, text: string): DraftContent {
  const trimmed = text.trim();
  const match = trimmed.match(/^subject:\s*(.+?)\n([\s\S]*)$/i);
  if (match) {
    return {
      action_id: action.id,
      action_title: action.title,
      subject: match[1].trim(),
      body: match[2].trim(),
    };
  }
  return {
    action_id: action.id,
    action_title: action.title,
    subject: action.title,
    body: trimmed,
  };
}

export default function TopActions({ actions }: TopActionsProps) {
  const [draft, setDraft] = useState<DraftContent | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleDraft = async (action: ActionItem) => {
    setLoadingId(action.id);
    let content: DraftContent | null = null;

    // Live: generate on the GB10 from the action's evidence context.
    if (action.draft_kind && action.context) {
      const res = await postDraft({
        kind: action.draft_kind,
        context: action.context,
      });
      if (res?.draft) content = toDraftContent(action, res.draft);
    }

    // Offline fallback only.
    if (!content) {
      content =
        DEMO_DRAFTS[action.id] ?? {
          action_id: action.id,
          action_title: action.title,
          subject: action.title,
          body: "Draft unavailable offline — start the backend (bash serve.sh).",
        };
    }

    setDraft(content);
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
