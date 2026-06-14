import type { DraftContent } from "../types";

interface DraftModalProps {
  draft: DraftContent;
  onClose: () => void;
}

export default function DraftModal({ draft, onClose }: DraftModalProps) {
  const handleCopy = () => {
    navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`);
  };

  return (
    <div className="draft-overlay" onClick={onClose}>
      <div className="draft-modal" onClick={(e) => e.stopPropagation()}>
        <div className="draft-modal__header">
          <span className="draft-modal__title">Generated Draft</span>
          <button type="button" className="draft-modal__close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="draft-modal__subject">{draft.subject}</div>
        <div className="draft-modal__body">{draft.body}</div>
        <div className="draft-modal__actions">
          <button type="button" className="btn btn--primary btn--sm" onClick={handleCopy}>
            Copy to clipboard
          </button>
          <button type="button" className="btn btn--ghost btn--sm" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
