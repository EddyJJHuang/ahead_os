import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  postPmAsk,
  postPmAskStream,
  postPmAutonomyTask,
  postPmAutonomyTaskPreview,
} from "../api/client";
import type { ChatMessage, TaskPreview } from "../api/pm_types";
import {
  DEMO_ACTIVITY_FEED,
  DEMO_CHAT_FALLBACK,
  DEMO_CHAT_OFFLINE,
} from "../mock/demoData";
import type { ActivityFeedItem } from "../types";
import {
  createActivityItem,
  toolCallActivity,
  toolResultActivity,
} from "../utils/activityFeed";
import AgentActivityFeed from "./AgentActivityFeed";
import AgentTrace from "./AgentTrace";
import Markdown from "./Markdown";

const SUGGESTED_PROMPTS = [
  "Can we ship Friday?",
  "What is blocking launch?",
  "Every 30 min, watch Jira & email for P0s",
];

// Heuristic gate: when a message looks like an automation/recurring request, we
// ask the backend to propose a task spec (the model does the real parsing).
const TASK_INTENT_PATTERNS: RegExp[] = [
  /every\s+\d+\s*(min|minute|hour|hr|day|week)/i,
  /\b(recurring|periodically|every day|daily|hourly|weekly|on a schedule|automate|automatically)\b/i,
  /\b(remind me|keep an eye|watch for|monitor|track|check\s+\w+\s+(every|each))\b/i,
];

function detectTaskIntent(text: string): boolean {
  return TASK_INTENT_PATTERNS.some((re) => re.test(text));
}

function formatCadence(min: number): string {
  if (min < 60) return `every ${min} min`;
  if (min % 1440 === 0) return min === 1440 ? "daily" : `every ${min / 1440} days`;
  if (min % 60 === 0) return min === 60 ? "hourly" : `every ${min / 60} h`;
  return `every ${min} min`;
}

const SRC_LABEL: Record<string, string> = {
  jira: "Jira",
  github: "GitHub",
  emails: "Email",
  email: "Email",
  calendar: "Calendar",
  tasks: "Tasks",
  slack: "Slack",
};
const srcLabel = (s: string): string => SRC_LABEL[s] ?? s;

interface UiMessage {
  role: "user" | "assistant";
  text: string;
}

type LaunchState = "idle" | "launching" | "launched" | "error";

interface AskPMOSProps {
  backendReachable: boolean;
  modelReady: boolean;
  usingMockPanels: boolean;
  onTaskCreated?: () => void;
  externalActivities?: ActivityFeedItem[];
}

export default function AskPMOS({
  backendReachable,
  modelReady,
  usingMockPanels,
  onTaskCreated,
  externalActivities = [],
}: AskPMOSProps) {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [display, setDisplay] = useState<UiMessage[]>([]);
  const [traceSteps, setTraceSteps] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [usingLiveAgent, setUsingLiveAgent] = useState(false);
  const [liveActivities, setLiveActivities] = useState<ActivityFeedItem[]>([]);
  const analysisLogged = useRef(false);

  // Recurring-task proposal surfaced inside the chat.
  const [proposal, setProposal] = useState<TaskPreview | null>(null);
  const [proposalLoading, setProposalLoading] = useState(false);
  const [launchState, setLaunchState] = useState<LaunchState>("idle");

  // Keep the conversation pinned to the latest content, like a normal chatbot.
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [display, streamingText, traceSteps, proposal, proposalLoading, loading]);

  useEffect(() => {
    if (usingMockPanels || analysisLogged.current) return;
    analysisLogged.current = true;
    setLiveActivities([
      createActivityItem("Launch risk recalculated", "scan"),
      createActivityItem("Recommended decision updated", "decision"),
    ]);
  }, [usingMockPanels]);

  const appendActivity = useCallback((item: ActivityFeedItem) => {
    setLiveActivities((prev) => [item, ...prev]);
  }, []);

  // When a message looks like an automation request, ask the backend (model) to
  // propose a recurring-task spec; surface it as a confirm-to-launch card.
  const maybeProposeTask = useCallback(
    async (question: string) => {
      if (!backendReachable || !detectTaskIntent(question)) return;
      setProposal(null);
      setLaunchState("idle");
      setProposalLoading(true);
      appendActivity(createActivityItem("Recurring-task intent detected", "scan"));
      const preview = await postPmAutonomyTaskPreview(question);
      setProposalLoading(false);
      if (preview) setProposal(preview);
    },
    [backendReachable, appendActivity]
  );

  const handleLaunchTask = useCallback(async () => {
    if (!proposal) return;
    setLaunchState("launching");
    appendActivity(
      createActivityItem(`Launching "${proposal.title}" on NemoClaw…`, "tool")
    );
    setDisplay((prev) => [
      ...prev,
      {
        role: "assistant",
        text: `⏳ Commanding NemoClaw to launch "${proposal.title}"…`,
      },
    ]);
    const res = await postPmAutonomyTask({ request: proposal.request });
    if (res?.task) {
      const t = res.task;
      const cadence = formatCadence(t.cadence_minutes);
      const nextRun = t.next_run_at
        ? new Date(t.next_run_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })
        : "shortly";
      const scope = t.source_scope.map(srcLabel).join(", ");
      setLaunchState("launched");
      setDisplay((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `✅ Launched on NemoClaw — "${t.title}". Runs ${cadence}; next run ~${nextRun}. Watching: ${scope}. Review it under Scheduled Tasks (top-right).`,
        },
      ]);
      appendActivity(
        createActivityItem(`Task launched: ${t.title} (${cadence})`, "decision")
      );
      setProposal(null);
      onTaskCreated?.();
    } else {
      setLaunchState("error");
      setDisplay((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "⚠️ Could not launch the task — backend error. Please try again.",
        },
      ]);
      appendActivity(createActivityItem("Task launch failed", "alert"));
    }
  }, [proposal, appendActivity, onTaskCreated]);

  const feedItems = useMemo(() => {
    const live = [...externalActivities, ...liveActivities];
    return live.length > 0
      ? [...live, ...DEMO_ACTIVITY_FEED]
      : DEMO_ACTIVITY_FEED;
  }, [externalActivities, liveActivities]);

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
    appendActivity(
      createActivityItem(`Question received: "${question.trim()}"`, "tool")
    );

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
          appendActivity(toolCallActivity(event.name));
        } else if (event.type === "tool_result") {
          steps.push(`${event.name} returned`);
          setTraceSteps([...steps]);
          appendActivity(toolResultActivity(event.name));
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      });

      setUsingLiveAgent(true);
      setDisplay((prev) => [...prev, { role: "assistant", text: answer }]);
      setHistory((prev) => [...prev, { role: "assistant", content: answer }]);
      appendActivity(createActivityItem("Agent response completed", "decision"));
    } catch {
      const res = await postPmAsk({ messages: nextHistory });
      if (res?.answer) {
        setUsingLiveAgent(true);
        setDisplay((prev) => [...prev, { role: "assistant", text: res.answer }]);
        setHistory((prev) => [...prev, { role: "assistant", content: res.answer }]);
        appendActivity(createActivityItem("Agent response completed", "decision"));
        for (const step of res.trace) {
          if (step.type === "tool_call") appendActivity(toolCallActivity(step.name));
          if (step.type === "tool_result") appendActivity(toolResultActivity(step.name));
        }
      } else {
        showDemoAnswer(question);
      }
    } finally {
      setStreamingText("");
      setLoading(false);
      void maybeProposeTask(question);
    }
  };

  const statusHint = !backendReachable
    ? "Backend offline — demo answers only."
    : !modelReady
      ? "Model loading — demo answers until vLLM is ready."
      : usingLiveAgent
        ? "Live PM OS agent on :8100."
        : "Live PM OS agent on :8100 — ready.";

  return (
    <div className="chat">
      <p className="chat__status-line">{statusHint}</p>

      <div className="chat__messages">
        {display.length === 0 && !loading && (
          <p className="chat__hint">
            Ask follow-ups about the launch decision.
          </p>
        )}
        {display.map((msg, i) => (
          <div
            key={i}
            className={`chat__message chat__message--${msg.role === "user" ? "user" : "agent"}`}
          >
            {msg.role === "user" ? msg.text : <Markdown>{msg.text}</Markdown>}
          </div>
        ))}
        {loading && streamingText && (
          <div className="chat__message chat__message--agent">
            <Markdown>{streamingText}</Markdown>
          </div>
        )}
        {loading && traceSteps.length > 0 && <AgentTrace steps={traceSteps} />}
        {loading && !streamingText && traceSteps.length === 0 && (
          <p className="chat__thinking">Thinking…</p>
        )}

        {proposalLoading && (
          <div className="task-proposal task-proposal--loading">
            <span className="task-proposal__spinner" aria-hidden />
            Detecting a recurring task…
          </div>
        )}

        {proposal && launchState !== "launched" && (
          <div className="task-proposal">
            <div className="task-proposal__head">
              <span className="task-proposal__badge">Recurring task</span>
              <span className="task-proposal__title">{proposal.title}</span>
            </div>
            <div className="task-proposal__meta">
              <span>⏱ {formatCadence(proposal.cadence_minutes)}</span>
              <span>
                {proposal.task_type === "creative"
                  ? "Generates a deliverable"
                  : "Monitors & alerts"}
              </span>
              <span>{proposal.source_scope.map(srcLabel).join(" · ")}</span>
            </div>
            <p className="task-proposal__hint">
              Launch on NemoClaw to run this automatically in the local sandbox.
            </p>
            <div className="task-proposal__actions">
              <button
                type="button"
                className="btn btn--primary"
                onClick={handleLaunchTask}
                disabled={launchState === "launching"}
              >
                {launchState === "launching"
                  ? "Launching…"
                  : "▶ Launch recurring task"}
              </button>
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() => setProposal(null)}
                disabled={launchState === "launching"}
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {display.length === 0 && (
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
      )}

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

      <div className="chat__activity-divider" />

      <AgentActivityFeed
        items={feedItems}
        showLiveBadge={externalActivities.length > 0 || liveActivities.length > 0}
        showDemoBadge={externalActivities.length === 0 && liveActivities.length === 0}
        maxItems={5}
        compact
      />
    </div>
  );
}
