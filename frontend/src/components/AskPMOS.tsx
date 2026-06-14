import { useCallback, useState } from "react";
import { postPmAsk, postPmAskStream } from "../api/client";
import type { ChatMessage } from "../api/pm_types";
import { DEMO_CHAT_FALLBACK, DEMO_CHAT_OFFLINE } from "../mock/demoData";
import AgentTrace from "./AgentTrace";

const SUGGESTED_PROMPTS = [
  "Can we ship Friday?",
  "What changed overnight?",
  "What is blocking launch?",
];

interface UiMessage {
  role: "user" | "assistant";
  text: string;
}

interface AskPMOSProps {
  backendReachable: boolean;
  modelReady: boolean;
}

export default function AskPMOS({
  backendReachable,
  modelReady,
}: AskPMOSProps) {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [display, setDisplay] = useState<UiMessage[]>([]);
  const [traceSteps, setTraceSteps] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [usingLiveAgent, setUsingLiveAgent] = useState(false);

  const offlineFallback = useCallback((question: string): string => {
    const key = question.toLowerCase();
    for (const [pattern, answer] of Object.entries(DEMO_CHAT_FALLBACK)) {
      if (key.includes(pattern)) return answer;
    }
    return DEMO_CHAT_OFFLINE;
  }, []);

  const showDemoAnswer = (question: string) => {
    setUsingLiveAgent(false);
    setDisplay((prev) => [
      ...prev,
      { role: "assistant", text: offlineFallback(question) },
    ]);
  };

  const sendQuestion = async (question: string) => {
    if (!question.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: question };
    const nextHistory = [...history, userMsg];

    setDisplay((prev) => [...prev, { role: "user", text: question }]);
    setHistory(nextHistory);
    setInput("");
    setLoading(true);
    setTraceSteps([]);
    setStreamingText("");

    if (!backendReachable || !modelReady) {
      showDemoAnswer(question);
      setLoading(false);
      return;
    }

    try {
      let answer = "";
      const steps: string[] = [];

      await postPmAskStream({ messages: nextHistory }, (event) => {
        if (event.type === "token") {
          answer += event.text;
          setStreamingText(answer);
        } else if (event.type === "tool_call") {
          steps.push(`Calling ${event.name}…`);
          setTraceSteps([...steps]);
        } else if (event.type === "tool_result") {
          steps.push(`${event.name} returned`);
          setTraceSteps([...steps]);
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      });

      setUsingLiveAgent(true);
      setDisplay((prev) => [...prev, { role: "assistant", text: answer }]);
      setHistory((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch {
      const res = await postPmAsk({ messages: nextHistory });
      if (res?.answer) {
        setUsingLiveAgent(true);
        setDisplay((prev) => [...prev, { role: "assistant", text: res.answer }]);
        setHistory((prev) => [...prev, { role: "assistant", content: res.answer }]);
      } else {
        showDemoAnswer(question);
      }
    } finally {
      setStreamingText("");
      setLoading(false);
    }
  };

  const statusHint =
    !backendReachable
      ? "Backend offline — demo answers only."
      : !modelReady
        ? "Model loading — demo answers until vLLM is ready."
        : "Live PM OS agent on :8100.";

  return (
    <div className="chat">
      {usingLiveAgent && (
        <span className="chat-live-indicator">Live agent</span>
      )}

      <div className="chat__messages">
        {display.length === 0 && !loading && (
          <p className="chat__hint">{statusHint}</p>
        )}
        {display.map((msg, i) => (
          <div
            key={i}
            className={`chat__message chat__message--${msg.role === "user" ? "user" : "agent"}`}
          >
            {msg.text}
          </div>
        ))}
        {loading && streamingText && (
          <div className="chat__message chat__message--agent">{streamingText}</div>
        )}
        {loading && traceSteps.length > 0 && <AgentTrace steps={traceSteps} />}
        {loading && !streamingText && traceSteps.length === 0 && (
          <p className="chat__thinking">Thinking…</p>
        )}
      </div>

      <div className="chat__prompts">
        <span className="chat__prompts-label">Suggested</span>
        {SUGGESTED_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="prompt-chip"
            onClick={() => sendQuestion(prompt)}
            disabled={loading}
          >
            {prompt}
          </button>
        ))}
      </div>

      <form
        className="chat__input-row"
        onSubmit={(e) => {
          e.preventDefault();
          sendQuestion(input);
        }}
      >
        <input
          className="chat__input"
          placeholder="Ask PM OS…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="btn btn--primary"
          disabled={loading || !input.trim()}
        >
          Ask
        </button>
      </form>
    </div>
  );
}
