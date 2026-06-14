import type { ActivityFeedIcon, ActivityFeedItem } from "../types";

const ICON_GLYPH: Record<ActivityFeedIcon, string> = {
  alert: "!",
  scan: "◎",
  link: "⇄",
  gap: "○",
  draft: "✎",
  decision: "◆",
  tool: "●",
};

interface AgentActivityFeedProps {
  items: ActivityFeedItem[];
  showLiveBadge: boolean;
  showDemoBadge: boolean;
  maxItems?: number;
  compact?: boolean;
}

export default function AgentActivityFeed({
  items,
  showLiveBadge,
  showDemoBadge,
  maxItems = 5,
  compact = false,
}: AgentActivityFeedProps) {
  const visible = items.slice(0, maxItems);

  return (
    <div className={compact ? "activity-feed-wrap activity-feed-wrap--compact" : "activity-feed-wrap"}>
      <div className="activity-feed__header">
        <span className="activity-feed__title">Recent Agent Activity</span>
        <div className="activity-feed__badges">
          {showLiveBadge && (
            <span className="panel-badge panel-badge--live panel-badge--inline">
              Live
            </span>
          )}
          {showDemoBadge && (
            <span className="panel-badge panel-badge--demo panel-badge--inline">
              Demo fallback
            </span>
          )}
        </div>
      </div>

      <ul className={`activity-feed ${compact ? "activity-feed--compact" : ""}`}>
        {visible.map((item, index) => (
          <li
            key={item.id}
            className={`activity-feed__item ${index < visible.length - 1 ? "activity-feed__item--divider" : ""}`}
          >
            <span
              className={`activity-feed__icon activity-feed__icon--${item.icon}`}
              aria-hidden
            >
              {ICON_GLYPH[item.icon]}
            </span>
            <div className="activity-feed__content">
              <span className="activity-feed__time">{item.time}</span>
              <span className="activity-feed__text">{item.text}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
