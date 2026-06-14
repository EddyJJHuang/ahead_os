import type {
  ChatRequest,
  ChatResponse,
  ChatStreamEvent,
  ConfigResponse,
  HealthResponse,
  PmAnalysisResponse,
  PmAskRequest,
  PmAskResponse,
  PmDraftRequest,
  PmDraftResponse,
  RagRequest,
  RagResponse,
  SqlRequest,
  SqlResponse,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8100";

async function fetchJSON<T>(
  path: string,
  options?: RequestInit
): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function getHealth(): Promise<HealthResponse | null> {
  return fetchJSON<HealthResponse>("/health");
}

export async function getConfig(): Promise<ConfigResponse | null> {
  return fetchJSON<ConfigResponse>("/api/config");
}

export async function postRag(body: RagRequest): Promise<RagResponse | null> {
  return fetchJSON<RagResponse>("/api/rag", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function postSql(body: SqlRequest): Promise<SqlResponse | null> {
  return fetchJSON<SqlResponse>("/api/sql", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function postChat(body: ChatRequest): Promise<ChatResponse | null> {
  return fetchJSON<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// --- Local PM OS endpoints (the product) ----------------------------------

/** Run the PM triage workflow — powers Executive Decision + Top Actions + Evidence. */
export async function postAnalysis(): Promise<PmAnalysisResponse | null> {
  return fetchJSON<PmAnalysisResponse>("/api/pm/analysis", { method: "POST" });
}

/** Generate a draft (Slack/email/memo/...) live from an action's context. */
export async function postDraft(
  body: PmDraftRequest
): Promise<PmDraftResponse | null> {
  return fetchJSON<PmDraftResponse>("/api/pm/draft", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** Evidence-grounded PM Q&A (non-streaming fallback). */
export async function postPmAsk(
  body: PmAskRequest
): Promise<PmAskResponse | null> {
  return fetchJSON<PmAskResponse>("/api/pm/ask", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** Read an SSE stream of `data: {json}` frames and dispatch each parsed event. */
async function streamSSE(
  path: string,
  body: unknown,
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok || !res.body) {
    throw new Error(`Stream failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const line = frame.split("\n").find((l) => l.startsWith("data:"));
      if (line) {
        onEvent(JSON.parse(line.slice(5).trim()) as ChatStreamEvent);
      }
    }
  }
}

/** Stream generic tool-calling chat via SSE. */
export async function postChatStream(
  body: ChatRequest,
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  return streamSSE("/api/chat/stream", body, onEvent);
}

/** Stream evidence-grounded PM Q&A via SSE (Ask PM OS panel). */
export async function postPmAskStream(
  body: PmAskRequest,
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  return streamSSE("/api/pm/ask/stream", body, onEvent);
}

export { API_URL };
