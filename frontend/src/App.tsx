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

  return (
    <div className="app">
      <nav className="top-nav">
        <div className="top-nav__brand">
          <div className="top-nav__logo">PM</div>
          <div>
            <div className="top-nav__title">Local PM OS</div>
            <div className="top-nav__subtitle">Executive launch intelligence</div>
          </div>
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
            <div className="panel__title">Top 3 Actions</div>
          </header>
          <div className="panel__body">
            {!loading && panels && <TopActions actions={panels.actions} />}
            {loading && (
              <p className="panel-loading">Loading actions…</p>
            )}
          </div>
        </section>

        <section className="panel panel--pink">
          <header className="panel__header">
            <div className="panel__label">Agent</div>
            <div className="panel__title">Ask PM OS</div>
          </header>
          <div className="panel__body panel__body--chat">
            <AskPMOS />
          </div>
        </section>

        <section className="panel panel--sky">
          <header className="panel__header">
            <div className="panel__label">Sources</div>
            <div className="panel__title">Evidence Drawer</div>
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
