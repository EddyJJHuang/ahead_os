import { useEffect, useState } from "react";
import AskPMOS from "./components/AskPMOS";
import EvidenceDrawer from "./components/EvidenceDrawer";
import ExecutiveDecision from "./components/ExecutiveDecision";
import TopActions from "./components/TopActions";
import { loadPanelData } from "./services/panelData";
import type { PanelLoadState } from "./types";

export default function App() {
  const [panels, setPanels] = useState<PanelLoadState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPanelData().then((data) => {
      setPanels(data);
      setLoading(false);
    });
  }, []);

  const online = panels?.backendReachable ?? false;
  const agentReady = panels?.backendReachable && panels?.modelReady;

  const statusLabel = !panels
    ? "Loading…"
    : !online
      ? "Offline — mock data"
      : agentReady
        ? "Agent connected"
        : "API up — model loading";

  const todayLabel = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

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

        <div className="top-nav__status">
          <span
            className={`status-dot ${agentReady ? "" : "status-dot--offline"}`}
          />
          {statusLabel}
        </div>
      </nav>

      <main className="dashboard">
        <section className="panel panel--lavender">
          <header className="panel__header">
            <div className="panel__label">Decision</div>
            <div className="panel__title">Executive Decision</div>
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
            {loading && (
              <p className="panel-loading">Loading actions…</p>
            )}
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
            />
          </div>
        </section>

        <section className="panel panel--sky">
          <header className="panel__header">
            <div className="panel__label">Context</div>
            <div className="panel__title">Context Hub</div>
          </header>
          <div className="panel__body">
            {!loading && panels && (
              <EvidenceDrawer items={panels.evidence} />
            )}
            {loading && (
              <p className="panel-loading">Loading evidence…</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
