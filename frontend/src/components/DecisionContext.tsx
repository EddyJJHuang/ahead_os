import type { ReactNode } from "react";
import { Calendar, FileText, ListChecks } from "lucide-react";
import { siGithub, siGmail, siJira } from "simple-icons";
import type { SimpleIcon } from "simple-icons";

const ICON_SIZE = 16;

type SourceDef =
  | { id: string; label: string; kind: "simple"; icon: SimpleIcon }
  | { id: string; label: string; kind: "slack" }
  | {
      id: string;
      label: string;
      kind: "lucide";
      lucide: "calendar" | "tasks" | "docs";
    };

const DECISION_SOURCES: SourceDef[] = [
  { id: "jira", label: "Jira", kind: "simple", icon: siJira },
  { id: "github", label: "GitHub", kind: "simple", icon: siGithub },
  { id: "email", label: "Email", kind: "simple", icon: siGmail },
  { id: "calendar", label: "Calendar", kind: "lucide", lucide: "calendar" },
  { id: "tasks", label: "Tasks", kind: "lucide", lucide: "tasks" },
  { id: "docs", label: "Docs", kind: "lucide", lucide: "docs" },
  { id: "slack", label: "Slack", kind: "slack" },
];

const SOURCE_LABELS = DECISION_SOURCES.map((source) => source.label);

function SimpleSourceIcon({ icon }: { icon: SimpleIcon }) {
  return (
    <svg
      role="img"
      viewBox="0 0 24 24"
      width={ICON_SIZE}
      height={ICON_SIZE}
      className="decision-context__icon"
      aria-hidden
    >
      <path fill="currentColor" d={icon.path} />
    </svg>
  );
}

function SlackSourceIcon() {
  return (
    <svg
      role="img"
      viewBox="0 0 24 24"
      width={ICON_SIZE}
      height={ICON_SIZE}
      className="decision-context__icon"
      aria-hidden
    >
      <path
        fill="currentColor"
        d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.528 2.528 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.528 2.528 0 0 1 24 17.688a2.528 2.528 0 0 1-2.522 2.523h-6.313z"
      />
    </svg>
  );
}

function LucideSourceIcon({ children }: { children: ReactNode }) {
  return <span className="decision-context__icon">{children}</span>;
}

function renderLucideIcon(lucide: "calendar" | "tasks" | "docs") {
  switch (lucide) {
    case "calendar":
      return <Calendar size={ICON_SIZE} strokeWidth={1.75} />;
    case "tasks":
      return <ListChecks size={ICON_SIZE} strokeWidth={1.75} />;
    default:
      return <FileText size={ICON_SIZE} strokeWidth={1.75} />;
  }
}

export default function DecisionContext() {
  return (
    <div className="decision-context">
      <span className="decision-context__label">Decision context</span>
      <span className="decision-context__count">7 Sources Analyzed</span>

      <div className="decision-context__grid">
        {DECISION_SOURCES.map((source) => (
          <div key={source.id} className="decision-context__source">
            {source.kind === "simple" ? (
              <SimpleSourceIcon icon={source.icon} />
            ) : source.kind === "slack" ? (
              <SlackSourceIcon />
            ) : (
              <LucideSourceIcon>{renderLucideIcon(source.lucide)}</LucideSourceIcon>
            )}
            <span>{source.label}</span>
          </div>
        ))}
      </div>

      <p className="decision-context__footnote">
        This recommendation was generated from: {SOURCE_LABELS.join(" • ")}
      </p>
    </div>
  );
}
