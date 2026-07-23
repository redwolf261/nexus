import React from "react";

export interface NotificationDigest {
  digest_id: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
  collapsed_count: int;
  summary_message: string;
  target_ids: string[];
  timestamp: string;
}

interface NotificationToastProps {
  notifications: NotificationDigest[];
  onDismiss?: (id: string) => void;
}

export const NotificationToast: React.FC<NotificationToastProps> = ({ notifications, onDismiss }) => {
  if (!notifications || notifications.length === 0) return null;

  const getSeverityStyle = (prio: string) => {
    switch (prio.toUpperCase()) {
      case "CRITICAL":
        return "bg-rose-950/90 border-rose-600 text-rose-200";
      case "HIGH":
        return "bg-amber-950/90 border-amber-600 text-amber-200";
      case "MEDIUM":
        return "bg-sky-950/90 border-sky-600 text-sky-200";
      default:
        return "bg-slate-900/90 border-slate-700 text-slate-300";
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full">
      {notifications.map((n) => (
        <div
          key={n.digest_id}
          className={`p-3.5 rounded-lg border shadow-xl flex items-start justify-between gap-3 text-xs transition-all duration-200 ${getSeverityStyle(n.priority)}`}
        >
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 font-bold tracking-wide">
              <span>[{n.priority.toUpperCase()}]</span>
              {n.collapsed_count > 1 && (
                <span className="bg-white/10 px-1.5 py-0.5 rounded text-[10px]">
                  {n.collapsed_count} Collapsed
                </span>
              )}
            </div>
            <p className="text-slate-200 leading-relaxed">{n.summary_message}</p>
          </div>
          {onDismiss && (
            <button
              onClick={() => onDismiss(n.digest_id)}
              className="text-slate-400 hover:text-white font-bold p-1 text-sm leading-none"
            >
              ×
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

export default NotificationToast;
