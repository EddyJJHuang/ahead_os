import {
  siGithub,
  siGmail,
  siGooglecalendar,
  siGoogledocs,
  siJira,
} from "simple-icons";
import type { SimpleIcon } from "simple-icons";

type CustomIconId = "checklist" | "document";

const SIMPLE_ICON_MAP: Record<string, SimpleIcon> = {
  jira: siJira,
  github: siGithub,
  email: siGmail,
  gmail: siGmail,
  calendar: siGooglecalendar,
  googlecalendar: siGooglecalendar,
  docs: siGoogledocs,
  doc: siGoogledocs,
  knowledge: siGoogledocs,
};

const CUSTOM_ICON_MAP: Record<string, CustomIconId> = {
  tasks: "checklist",
  task: "checklist",
};

export function normalizeSourceKey(source: string): string {
  return source.toLowerCase().replace(/\s+/g, "");
}

export function hasSourceIcon(source: string): boolean {
  const key = normalizeSourceKey(source);
  if (key === "all" || key === "slack") return false;
  return key in SIMPLE_ICON_MAP || key in CUSTOM_ICON_MAP;
}

interface SourceIconProps {
  source: string;
  size?: number;
  className?: string;
}

function ChecklistIcon({ size, className }: { size: number; className?: string }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
    >
      <path
        d="M9 11.5 10.5 13l3.5-4M8 6.5h8M8 11.5h6M8 16.5h7"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function SourceIcon({
  source,
  size = 14,
  className = "source-icon",
}: SourceIconProps) {
  const key = normalizeSourceKey(source);
  const custom = CUSTOM_ICON_MAP[key];

  if (custom === "checklist") {
    return <ChecklistIcon size={size} className={className} />;
  }

  const icon = SIMPLE_ICON_MAP[key];
  if (!icon) return null;

  return (
    <svg
      role="img"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      style={{ color: `#${icon.hex}` }}
      aria-hidden
    >
      <path fill="currentColor" d={icon.path} />
    </svg>
  );
}
