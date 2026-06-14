import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import AskPMOS from "./components/AskPMOS";
import EvidenceDrawer from "./components/EvidenceDrawer";
import ExecutiveDecision from "./components/ExecutiveDecision";
import ScheduledTasksModal from "./components/ScheduledTasksModal";
import TopActions from "./components/TopActions";
import {
  getPmAutonomyStatus,
  getPmDemoStatus,
  getPmEmergencyStatus,
  postPmAutonomyRunTask,
  postPmDemoIngest,
  postPmEmergencyToggle,
} from "./api/client";
import type { AutonomyStatusResponse, DemoContextItem } from "./api/pm_types";
import { loadPanelData } from "./services/panelData";
import type { ActivityFeedItem, EvidenceItem, PanelLoadState } from "./types";
import { createActivityItem } from "./utils/activityFeed";

const REFRESH_MS = 25_000;
const INGEST_MS = 20_000;

const SOURCE_LABELS: Record<string, string> = {
  jira: "Jira",
  github: "GitHub",
  emails: "Email",
  slack: "Slack",
  calendar: "Calendar",
  tasks: "Tasks",
};

function mapContextItem(item: DemoContextItem): EvidenceItem {
  return {
    id: item.id,
    source: item.source,
    title: item.title,
    snippet: item.snippet,
    detail: item.detail,
    severity: item.severity,
    origin: item.origin,
  };
}

export default function App() {
  const [panels, setPanels] = useState<PanelLoadState | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const [autonomy, setAutonomy] = useState<AutonomyStatusResponse | null>(null);
  const [showTasks, setShowTasks] = useState(false);
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null);

  const [emergencyActive, setEmergencyActive] = useState(false);
  const [extraEvidence, setExtraEvidence] = useState<EvidenceItem[]>([]);
  const [demoActivities, setDemoActivities] = useState<ActivityFeedItem[]>([]);

  const inFlight = useRef(false);
  const ingestInFlight = useRef(false);

  const refreshPanels = useCallback(async (initial = false) => {
    if (inFlight.current) return;
    inFlight.current = true;
    try {
      const data = await loadPanelData();
      setPanels((prev) =>
        !initial && prev && !prev.usingMockPanels && data.usingMockPanels
          ? prev
          : data
      );
      if (!data.usingMockPanels || initial) setLastUpdated(new Date());
    } finally {
      inFlight.current = false;
      if (initial) setLoading(false);
    }
  }, []);

  const refreshAutonomy = useCallback(async () => {
    const status = await getPmAutonomyStatus();
    if (status) setAutonomy(status);
  }, []);

  const appendDemoActivity = useCallback((text: string, icon: ActivityFeedItem["icon"] = "scan") => {
    setDemoActivities((prev) => [createActivityItem(text, icon, true), ...prev].slice(0, 20));
  }, []);

  const ingestPeacetimeSignal = useCallback(async () => {
    if (ingestInFlight.current || emergencyActive) return;
    ingestInFlight.current = true;
    try {
      const result = await postPmDemoIngest();
      if (!result?.ingested || !result.signal) return;

      const signal = result.signal;
      if (!signal) return;

      const label = SOURCE_LABELS[signal.source] ?? signal.source;
      setExtraEvidence((prev) => {
        const item = mapContextItem(signal.context_item);
        if (prev.some((entry) => entry.id === item.id)) return prev;
        return [item, ...prev];
      });
      appendDemoActivity(`Ingested ${label} signal — ${signal.context_item.title}`, "link");
      appendDemoActivity("Launch risk recalculated", "scan");
      await refreshPanels();
      await refreshAutonomy();
    } finally {
      ingestInFlight.current = false;
    }
  }, [appendDemoActivity, emergencyActive, refreshAutonomy, refreshPanels]);

  const handleEmergencyTrigger = useCallback(async () => {
    if (emergencyActive) return;
    const result = await postPmEmergencyToggle(true);
    if (!result) return;
    setEmergencyActive(true);
    appendDemoActivity("Emergency overlay activated", "alert");
    appendDemoActivity("Emergency records merged into PM OS", "scan");
    appendDemoActivity("Launch risk recalculated", "scan");
    appendDemoActivity("Recommended decision updated", "decision");
    await refreshPanels();
    await refreshAutonomy();
  }, [appendDemoActivity, emergencyActive, refreshAutonomy, refreshPanels]);

  useEffect(() => {
    void refreshPanels(true);
    void refreshAutonomy();
    void getPmEmergencyStatus().then((status) => {
      if (status) setEmergencyActive(status.emergency_active);
    });
    void getPmDemoStatus();
  }, [refreshAutonomy, refreshPanels]);

  useEffect(() => {
    const id = setInterval(() => {
      void refreshPanels();
      void refreshAutonomy();
    }, REFRESH_MS);
    return () => clearInterval(id);
  }, [refreshAutonomy, refreshPanels]);

  useEffect(() => {
    if (!panels?.backendReachable || emergencyActive || panels.usingMockPanels) return;
    const id = setInterval(() => {
      void ingestPeacetimeSignal();
    }, INGEST_MS);
    return () => clearInterval(id);
  }, [emergencyActive, ingestPeacetimeSignal, panels?.backendReachable, panels?.usingMockPanels]);

  const handleTaskCreated = useCallback(() => {
    void refreshAutonomy();
    setShowTasks(true);
  }, [refreshAutonomy]);

  const handleRunNow = useCallback(
    async (taskId: string) => {
      setRunningTaskId(taskId);
      try {
        await postPmAutonomyRunTask(taskId);
        await refreshAutonomy();
      } finally {
        setRunningTaskId(null);
      }
    },
    [refreshAutonomy]
  );

  const evidenceItems = useMemo(() => {
    const analysisEvidence = panels?.evidence ?? [];
    const seen = new Set<string>();
    const merged: EvidenceItem[] = [];
    for (const item of [...extraEvidence, ...analysisEvidence]) {
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      merged.push(item);
    }
    return merged;
  }, [extraEvidence, panels?.evidence]);

  const online = panels?.backendReachable ?? false;
  const agentReady = panels?.backendReachable && panels?.modelReady;

  const statusLabel = !panels
    ? "Loading…"
    : !online
      ? "Offline — mock data"
      : agentReady
        ? "Agent connected"
        : "API up — model loading";

  const tasks = autonomy?.tasks ?? [];
  const pollSeconds = autonomy?.scheduler?.poll_seconds ?? 20;

  const todayLabel = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const updatedLabel = lastUpdated
    ? lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : null;

  return (
    <div className="app">
      <nav className="top-nav">
        <div className="top-nav__brand">
          <img
            className="top-nav__logo-img"
            src="/local-pm-os-logo.png"
            alt="Local PM OS"
          />
        </div>

        <div className="top-nav__greeting">
          <span className="top-nav__hello">Good morning, Nikkie</span>
          <span className="top-nav__date">{todayLabel}</span>
        </div>

        <div className="top-nav__right">
          <button
            type="button"
            className="demo-emergency-trigger"
            onClick={() => void handleEmergencyTrigger()}
            disabled={emergencyActive || !online}
            title={
              emergencyActive
                ? "Emergency scenario active"
                : "Trigger emergency demo scenario"
            }
            aria-label="Trigger emergency demo scenario"
          />

          <button
            type="button"
            className="tasks-pill"
            onClick={() => setShowTasks(true)}
            title="Browse recurring tasks running on NemoClaw"
          >
            <span className="tasks-pill__icon" aria-hidden>
              ⏱
            </span>
            Scheduled Tasks
            <span className="tasks-pill__count">{tasks.length}</span>
          </button>

          <div className="top-nav__status">
            <span
              className={`status-dot ${agentReady ? "" : "status-dot--offline"}`}
            />
            {statusLabel}
          </div>
        </div>
      </nav>

      <main className="dashboard">
        <section className="panel panel--lavender">
          <header className="panel__header">
            <div>
              <div className="panel__label">Decision</div>
              <div className="panel__title">Executive Decision</div>
            </div>
            {online && (
              <div className="panel__live" title="Re-derived from the Context sources on a timer">
                <span className="panel__live-dot" />
                Live · auto-refresh {REFRESH_MS / 1000}s
                {updatedLabel ? ` · ${updatedLabel}` : ""}
              </div>
            )}
          </header>
          <div className="panel__body">
            <ExecutiveDecision
              data={panels?.executive ?? null}
              loading={loading}
              usingMock={panels?.usingMockPanels}
            />
          </div>
        </section>

        <section className="panel panel--cream">
          <header className="panel__header">
            <div className="panel__label">Actions</div>
            <div className="panel__title">Recommended Next Steps</div>
          </header>
          <div className="panel__body">
            {!loading && panels && (
              <TopActions
                actions={panels.actions}
                modelReady={panels.modelReady}
              />
            )}
            {loading && <p className="panel-loading">Loading actions…</p>}
          </div>
        </section>

        <section className="panel panel--pink panel--chat">
          <header className="panel__header">
            <div className="panel__label">Agent</div>
            <div className="panel__title">Ask PM OS</div>
          </header>
          <div className="panel__body panel__body--chat">
            <AskPMOS
              backendReachable={online}
              modelReady={panels?.modelReady ?? false}
              usingMockPanels={panels?.usingMockPanels ?? true}
              onTaskCreated={handleTaskCreated}
              externalActivities={demoActivities}
            />
          </div>
        </section>

        <section className="panel panel--sky">
          <header className="panel__header">
            <div className="panel__label">Context</div>
            <div className="panel__title">Context Hub</div>
          </header>
          <div className="panel__body">
            {!loading && panels && <EvidenceDrawer items={evidenceItems} />}
            {loading && <p className="panel-loading">Loading evidence…</p>}
          </div>
        </section>
      </main>

      {showTasks && (
        <ScheduledTasksModal
          tasks={tasks}
          pollSeconds={pollSeconds}
          runtime={autonomy?.runtime ?? null}
          onClose={() => setShowTasks(false)}
          onRunNow={handleRunNow}
          runningId={runningTaskId}
        />
      )}
    </div>
  );
}
