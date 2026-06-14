import type {
  ChatRequest,
  ChatResponse,
  ChatStreamEvent,
  ConfigResponse,
  HealthResponse,
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

/** Stream chat via SSE (fetch + ReadableStream). */
export async function postChatStream(
  body: ChatRequest,
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  const res = await fetch(`${API_URL}/api/chat/stream`, {
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

export { API_URL };
