import React, { useEffect } from "react";
import { NotificationDTO } from "./NotificationCard";

interface NotificationToastProps {
  notification: NotificationDTO | null;
  onClose: () => void;
  autoCloseMs?: number;
}

export const NotificationToast: React.FC<NotificationToastProps> = ({
  notification,
  onClose,
  autoCloseMs = 5000,
}) => {
  useEffect(() => {
    if (!notification) return;
    const timer = setTimeout(() => {
      onClose();
    }, autoCloseMs);
    return () => clearTimeout(timer);
  }, [notification, autoCloseMs, onClose]);

  if (!notification) return null;

  const pr = String(notification.priority).toUpperCase();
  let bgClasses = "bg-slate-900 border-slate-700 text-slate-100";

  if (pr === "CRITICAL") {
    bgClasses = "bg-rose-950/95 border-rose-700 text-rose-100 shadow-2xl shadow-rose-950/80 animate-bounce";
  } else if (pr === "HIGH") {
    bgClasses = "bg-amber-950/95 border-amber-700 text-amber-100 shadow-xl shadow-amber-950/50";
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-sm w-full p-4 rounded-xl border shadow-2xl space-y-2 backdrop-blur-md transition-all font-mono">
      <div className={`p-3 rounded-lg border ${bgClasses}`}>
        <div className="flex items-center justify-between pb-1 border-b border-white/10">
          <span className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-current animate-ping" />
            {pr} ALERT
          </span>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-base leading-none">
            &times;
          </button>
        </div>

        <h5 className="font-semibold text-xs mt-2">{notification.title}</h5>
        <p className="text-[11px] opacity-90 mt-1 line-clamp-2">{notification.body}</p>

        <div className="text-[9px] opacity-75 mt-2 text-right">
          {new Date(notification.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};
