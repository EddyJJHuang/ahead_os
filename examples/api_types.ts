// api_types.ts — TypeScript contract for the Meridian Ops Agent API (port 8100).
// Hand-written to match api_server.py. For a generated version:
//   npx openapi-typescript http://<GB10_HOST>:8100/openapi.json -o src/api.d.ts

export type Role = "user" | "assistant" | "tool";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  max_rounds?: number; // default 5
}

export type TraceStep =
  | { type: "tool_call"; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; name: string; result: unknown }
  | { type: "assistant"; content: string };

export interface ChatResponse {
  answer: string;
  trace: TraceStep[];
}

// Server-Sent Events emitted by POST /api/chat/stream
export type ChatStreamEvent =
  | { type: "token"; text: string }
  | { type: "tool_call"; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; name: string; result: unknown }
  | { type: "error"; message: string }
  | { type: "done" };

export interface SqlRequest {
  question: string;
  max_rows?: number; // default 20
}

export interface SqlResponse {
  sql?: string;
  columns?: string[];
  rows?: Array<Array<string | number | null>>;
  error?: string;
  raw?: string;
}

export interface RagRequest {
  query: string;
  k?: number; // default 3
}

export interface RagHit {
  rank?: number;
  score?: number;
  source?: string;
  chunk_index?: number;
  text?: string;
  error?: string;
}

export interface RagResponse {
  hits: RagHit[];
}

export interface HealthResponse {
  status: string;
  model_id: string;
  vllm: boolean;
  mock: boolean;
}

export interface ConfigResponse {
  model_id: string;
  openai_base_url: string;
  mock_base_url: string;
  capabilities: Array<"chat" | "sql" | "rag">;
  tools: string[];
}

// --- tiny typed client (copy/adapt) ----------------------------------------
export class AgentClient {
  constructor(private base = "http://localhost:8100") {}

  async health(): Promise<HealthResponse> {
    return (await fetch(`${this.base}/health`)).json();
  }
  async sql(body: SqlRequest): Promise<SqlResponse> {
    return (await fetch(`${this.base}/api/sql`, this.post(body))).json();
  }
  async rag(body: RagRequest): Promise<RagResponse> {
    return (await fetch(`${this.base}/api/rag`, this.post(body))).json();
  }
  async chat(body: ChatRequest): Promise<ChatResponse> {
    return (await fetch(`${this.base}/api/chat`, this.post(body))).json();
  }
  /** Stream chat; calls onEvent for every SSE frame. */
  async chatStream(body: ChatRequest, onEvent: (e: ChatStreamEvent) => void): Promise<void> {
    const res = await fetch(`${this.base}/api/chat/stream`, this.post(body));
    const reader = res.body!.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const frames = buf.split("\n\n");
      buf = frames.pop() ?? "";
      for (const f of frames) {
        const line = f.split("\n").find((l) => l.startsWith("data:"));
        if (line) onEvent(JSON.parse(line.slice(5).trim()) as ChatStreamEvent);
      }
    }
  }
  private post(body: unknown): RequestInit {
    return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  }
}
