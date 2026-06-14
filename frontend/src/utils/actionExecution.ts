import type { ActionItem, ArtifactType, ExecutionArtifact } from "../types";

export function enrichAction(
  action: Pick<
    ActionItem,
    "id" | "title" | "rationale" | "draft_kind" | "explanation" | "ctaLabel" | "artifactType"
  >
): Pick<ActionItem, "explanation" | "ctaLabel" | "artifactType"> {
  if (action.explanation && action.ctaLabel && action.artifactType) {
    return {
      explanation: action.explanation,
      ctaLabel: action.ctaLabel,
      artifactType: action.artifactType,
    };
  }

  const id = action.id.toLowerCase();
  const title = action.title.toLowerCase();
  const explanation = action.rationale ?? action.explanation ?? "";

  if (
    id.includes("qa") ||
    title.includes("qa review") ||
    title.includes("checkout qa")
  ) {
    return {
      explanation,
      ctaLabel: "Generate Meeting",
      artifactType: "meeting",
    };
  }

  if (
    id.includes("cust") ||
    id.includes("globex") ||
    title.includes("globex") ||
    title.includes("customer") ||
    title.includes("stakeholder") ||
    title.includes("notify") ||
    action.draft_kind === "stakeholder_email"
  ) {
    return {
      explanation,
      ctaLabel: "Generate Email",
      artifactType: "email",
    };
  }

  if (
    id.includes("pr") ||
    title.includes("pr-") ||
    title.includes("review on pr")
  ) {
    return {
      explanation,
      ctaLabel: "Generate Review Request",
      artifactType: "review",
    };
  }

  return {
    explanation,
    ctaLabel: "Generate Email",
    artifactType: "email" as ArtifactType,
  };
}

export function draftToArtifact(
  action: ActionItem,
  draft: string
): ExecutionArtifact {
  const type = action.artifactType ?? "email";
  const id = action.id;

  if (type === "email") {
    return {
      type: "email",
      action_id: id,
      to: "vp-ops@globex.com",
      subject: action.title,
      body: draft,
    };
  }

  if (type === "meeting") {
    return {
      type: "meeting",
      action_id: id,
      title: action.title,
      datetime: "Wed, Jun 18 · 10:00 AM – 12:00 PM PT",
      attendees: "Sarah Chen (QA Lead), Alex Kim (Eng), You",
      agenda: draft,
    };
  }

  return {
    type: "review",
    action_id: id,
    target: "PR-88 · github.com/meridian/checkout#88",
    message: draft,
    reviewer: "@alex-kim",
  };
}
