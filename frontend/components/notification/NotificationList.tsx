import React, { useState } from "react";
import { NotificationCard, NotificationDTO } from "./NotificationCard";

interface NotificationListProps {
  notifications: NotificationDTO[];
  onAcknowledge?: (id: string) => void;
  onDismiss?: (id: string) => void;
  onSelectNotification?: (notif: NotificationDTO) => void;
  onRefresh?: () => void;
}

export const NotificationList: React.FC<NotificationListProps> = ({
  notifications,
  onAcknowledge,
  onDismiss,
  onSelectNotification,
  onRefresh,
}) => {
  const [filterPriority, setFilterPriority] = useState<string>("ALL");
  const [filterUnreadOnly, setFilterUnreadOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filtered = (notifications || []).filter((item) => {
    if (filterUnreadOnly && (item.acknowledged_at || item.dismissed_at)) return false;
    if (filterPriority !== "ALL" && String(item.priority).toUpperCase() !== filterPriority) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchBody = item.body.toLowerCase().includes(q);
      const matchId = item.notification_id.toLowerCase().includes(q);
      if (!matchTitle && !matchBody && !matchId) return false;
    }
    return true;
  });

  return (
    <div className="space-y-3 font-mono">
      {/* Header controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            Notifications ({filtered.length})
          </h3>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-medium rounded border border-slate-700"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
        <input
          type="text"
          placeholder="Filter by title/body..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 text-[11px] focus:outline-none focus:border-purple-500"
        />

        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 text-[11px] focus:outline-none focus:border-purple-500"
        >
          <option value="ALL">All Priorities</option>
          <option value="CRITICAL">CRITICAL Only</option>
          <option value="HIGH">HIGH Only</option>
          <option value="MEDIUM">MEDIUM Only</option>
          <option value="LOW">LOW Only</option>
        </select>

        <label className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-300 text-[11px] cursor-pointer">
          <input
            type="checkbox"
            checked={filterUnreadOnly}
            onChange={(e) => setFilterUnreadOnly(e.target.checked)}
            className="rounded bg-slate-900 border-slate-700 text-purple-600 focus:ring-0"
          />
          <span>Unread Only</span>
        </label>
      </div>

      {/* Items */}
      {filtered.length === 0 ? (
        <div className="text-xs text-slate-500 py-8 text-center bg-slate-950/40 rounded-lg border border-slate-800">
          No notifications match current criteria.
        </div>
      ) : (
        <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
          {filtered.map((item) => (
            <NotificationCard
              key={item.notification_id}
              notification={item}
              onAcknowledge={onAcknowledge}
              onDismiss={onDismiss}
              onClick={onSelectNotification}
            />
          ))}
        </div>
      )}
    </div>
  );
};
