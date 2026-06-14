import type { ActivityFeedIcon, ActivityFeedItem } from "../types";

export function formatActivityTime(date = new Date()): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

export function createActivityItem(
  text: string,
  icon: ActivityFeedIcon = "tool",
  live = true
): ActivityFeedItem {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    time: formatActivityTime(),
    text,
    icon,
    live,
  };
}

const TOOL_LABELS: Record<string, string> = {
  search_jira: "Jira",
  search_github: "GitHub",
  search_email: "Email",
  search_calendar: "Calendar",
  search_tasks: "Tasks",
  search_docs: "Knowledge base",
  retrieve_evidence: "Evidence retrieval",
  state_snapshot: "Launch state snapshot",
};

export function toolCallActivity(name: string): ActivityFeedItem {
  const label = TOOL_LABELS[name] ?? name.replace(/_/g, " ");
  return createActivityItem(`${label} scan started`, "scan");
}

export function toolResultActivity(name: string): ActivityFeedItem {
  const label = TOOL_LABELS[name] ?? name.replace(/_/g, " ");
  return createActivityItem(`${label} results matched`, "link");
}
