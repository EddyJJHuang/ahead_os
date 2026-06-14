import type { ExecutionArtifact } from "../types";

interface ExecutionArtifactModalProps {
  artifact: ExecutionArtifact;
  onClose: () => void;
  onPrimary: () => void;
}

function Field({
  label,
  value,
  multiline = false,
}: {
  label: string;
  value: string;
  multiline?: boolean;
}) {
  return (
    <div className="artifact-field">
      <span className="artifact-field__label">{label}</span>
      {multiline ? (
        <div className="artifact-field__value artifact-field__value--block">
          {value}
        </div>
      ) : (
        <span className="artifact-field__value">{value}</span>
      )}
    </div>
  );
}

export default function ExecutionArtifactModal({
  artifact,
  onClose,
  onPrimary,
}: ExecutionArtifactModalProps) {
  const shellClass =
    artifact.type === "email"
      ? "artifact-modal artifact-modal--email"
      : artifact.type === "meeting"
        ? "artifact-modal artifact-modal--meeting"
        : "artifact-modal artifact-modal--review";

  const title =
    artifact.type === "email"
      ? "Gmail draft"
      : artifact.type === "meeting"
        ? "Calendar event"
        : "Review request";

  const primaryLabel =
    artifact.type === "email"
      ? "Send"
      : artifact.type === "meeting"
        ? "Schedule"
        : "Post";

  return (
    <div className="draft-overlay" onClick={onClose}>
      <div
        className={`draft-modal ${shellClass}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="draft-modal__header">
          <span className="draft-modal__title">{title}</span>
          <button type="button" className="draft-modal__close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="artifact-modal__body">
          {artifact.type === "email" && (
            <>
              <Field label="To" value={artifact.to} />
              <Field label="Subject" value={artifact.subject} />
              <Field label="Body" value={artifact.body} multiline />
            </>
          )}
          {artifact.type === "meeting" && (
            <>
              <Field label="Title" value={artifact.title} />
              <Field label="Date/time" value={artifact.datetime} />
              <Field label="Attendees" value={artifact.attendees} />
              <Field label="Agenda" value={artifact.agenda} multiline />
            </>
          )}
          {artifact.type === "review" && (
            <>
              <Field label="Target PR" value={artifact.target} />
              <Field label="Reviewer" value={artifact.reviewer} />
              <Field label="Message" value={artifact.message} multiline />
            </>
          )}
        </div>

        <div className="draft-modal__actions">
          <button type="button" className="btn btn--ghost btn--sm">
            Edit
          </button>
          <button
            type="button"
            className="btn btn--primary btn--sm"
            onClick={onPrimary}
          >
            {primaryLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
