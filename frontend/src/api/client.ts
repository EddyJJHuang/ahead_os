import type {
  AnalysisResponse,
  AskResponse,
  AskStreamEvent,
  ChatMessage,
  DraftRequest,
  DraftResponse,
  SourceCounts,
  SourceName,
  SourceResponse,
} from "./pm_types";
import type { ConfigResponse, HealthResponse } from "./types";

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

export async function postPmAnalysis(): Promise<AnalysisResponse | null> {
  return fetchJSON<AnalysisResponse>("/api/pm/analysis", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function postPmAsk(body: {
  messages: ChatMessage[];
  max_rounds?: number;
}): Promise<AskResponse | null> {
  return fetchJSON<AskResponse>("/api/pm/ask", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function postPmDraft(
  body: DraftRequest
): Promise<DraftResponse | null> {
  return fetchJSON<DraftResponse>("/api/pm/draft", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getPmSources(): Promise<SourceCounts | null> {
  return fetchJSON<SourceCounts>("/api/pm/sources");
}

export async function getPmSource(
  source: SourceName
): Promise<SourceResponse | null> {
  return fetchJSON<SourceResponse>(`/api/pm/sources/${source}`);
}

/** Stream PM ask via SSE (fetch + ReadableStream). */
export async function postPmAskStream(
  body: { messages: ChatMessage[]; max_rounds?: number },
  onEvent: (event: AskStreamEvent) => void
): Promise<void> {
  const res = await fetch(`${API_URL}/api/pm/ask/stream`, {
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
        onEvent(JSON.parse(line.slice(5).trim()) as AskStreamEvent);
      }
    }
  }
}

export { API_URL };
