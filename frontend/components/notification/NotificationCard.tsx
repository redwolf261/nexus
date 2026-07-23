import React from "react";

export interface NotificationDTO {
  notification_id: str;
  title: str;
  body: str;
  event_type: str;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
  status: str;
  source_entity_type: str;
  source_entity_id: str;
  created_at: str;
  acknowledged_at?: str | null;
  dismissed_at?: str | null;
  version: number;
}

interface NotificationCardProps {
  notification: NotificationDTO;
  onAcknowledge?: (id: string) => void;
  onDismiss?: (id: string) => void;
  onClick?: (notification: NotificationDTO) => void;
}

export const NotificationCard: React.FC<NotificationCardProps> = ({
  notification,
  onAcknowledge,
  onDismiss,
  onClick,
}) => {
  const isUnread = !notification.acknowledged_at && !notification.dismissed_at;
  const pr = String(notification.priority).toUpperCase();

  let priorityBorder = "border-slate-800";
  let priorityBadge = "bg-slate-800 text-slate-300 border-slate-700";

  switch (pr) {
    case "CRITICAL":
      priorityBorder = "border-rose-800/80 bg-rose-950/20";
      priorityBadge = "bg-rose-950 text-rose-300 border-rose-800 animate-pulse";
      break;
    case "HIGH":
      priorityBorder = "border-amber-800/60 bg-amber-950/10";
      priorityBadge = "bg-amber-950 text-amber-300 border-amber-800";
      break;
    case "MEDIUM":
      priorityBorder = "border-cyan-800/40";
      priorityBadge = "bg-cyan-950 text-cyan-300 border-cyan-800";
      break;
    case "LOW":
      priorityBorder = "border-slate-800";
      priorityBadge = "bg-slate-900 text-slate-400 border-slate-800";
      break;
  }

  return (
    <div
      onClick={() => onClick?.(notification)}
      className={`p-3.5 rounded-lg border text-xs transition-all space-y-2 cursor-pointer ${priorityBorder} ${
        isUnread ? "bg-slate-900/90 shadow-md" : "bg-slate-950/60 opacity-75"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          {isUnread && <span className="w-2 h-2 rounded-full bg-purple-500 flex-shrink-0" />}
          <h4 className="font-semibold text-slate-100 line-clamp-1">{notification.title}</h4>
        </div>
        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${priorityBadge}`}>
          {pr}
        </span>
      </div>

      <p className="text-slate-300 leading-relaxed text-[11px] line-clamp-2">{notification.body}</p>

      <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[10px] text-slate-400 font-mono">
        <span className="text-cyan-400 font-bold">
          {notification.source_entity_type}: {notification.source_entity_id}
        </span>
        <span>{new Date(notification.created_at).toLocaleTimeString()}</span>
      </div>

      {(onAcknowledge || onDismiss) && isUnread && (
        <div className="flex justify-end gap-2 pt-1">
          {onDismiss && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(notification.notification_id);
              }}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-medium"
            >
              Dismiss
            </button>
          )}
          {onAcknowledge && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAcknowledge(notification.notification_id);
              }}
              className="px-2.5 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white text-[10px] font-medium shadow"
            >
              Acknowledge
            </button>
          )}
        </div>
      )}
    </div>
  );
};
