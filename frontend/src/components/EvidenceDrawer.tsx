import { useState } from "react";
import type { EvidenceItem } from "../types";

const SOURCES = ["All", "Jira", "GitHub", "Email", "Calendar", "Tasks", "Knowledge"] as const;

interface EvidenceDrawerProps {
  items: EvidenceItem[];
}

function sourceClass(source: string): string {
  const key = source.toLowerCase().replace(/\s+/g, "");
  return `evidence-card__source evidence-card__source--${key}`;
}

export default function EvidenceDrawer({ items }: EvidenceDrawerProps) {
  const [filter, setFilter] = useState<string>("All");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered =
    filter === "All" ? items : items.filter((item) => item.source === filter);

  const liveCount = items.filter((i) => i.origin === "live").length;

  return (
    <>
      {liveCount > 0 && (
        <span className="panel-badge panel-badge--live">
          {liveCount} live from KB
        </span>
      )}
      <div className="evidence-filters">
        {SOURCES.map((source) => (
          <button
            key={source}
            type="button"
            className={`filter-chip ${filter === source ? "filter-chip--active" : ""}`}
            onClick={() => setFilter(source)}
          >
            {source}
          </button>
        ))}
      </div>

      <div className="evidence-list">
        {filtered.map((item) => {
          const isExpanded = expandedId === item.id;
          return (
            <div
              key={item.id}
              className={`evidence-card ${isExpanded ? "evidence-card--expanded" : ""}`}
            >
              <button
                type="button"
                className="evidence-card__header"
                onClick={() => setExpandedId(isExpanded ? null : item.id)}
              >
                <span className={sourceClass(item.source)}>{item.source}</span>
                <div className="evidence-card__content">
                  <div className="evidence-card__title-row">
                    <span className="evidence-card__title">{item.title}</span>
                    {item.origin === "live" && (
                      <span className="origin-tag origin-tag--live">live</span>
                    )}
                  </div>
                  {!isExpanded && (
                    <div className="evidence-card__snippet">{item.snippet}</div>
                  )}
                </div>
                <span className="evidence-card__chevron">▼</span>
              </button>
              {isExpanded && (
                <div className="evidence-card__detail">{item.detail}</div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}
