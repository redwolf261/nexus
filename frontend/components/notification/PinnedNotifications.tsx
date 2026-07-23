import React from "react";
import { NotificationDTO } from "./NotificationCard";

interface PinnedNotificationsProps {
  pinnedItems: NotificationDTO[];
  onSelectNotification?: (notif: NotificationDTO) => void;
  onUnpin?: (id: string) => void;
}

export const PinnedNotifications: React.FC<PinnedNotificationsProps> = ({
  pinnedItems,
  onSelectNotification,
  onUnpin,
}) => {
  if (!pinnedItems || pinnedItems.length === 0) return null;

  return (
    <div className="bg-amber-950/20 border border-amber-800/40 rounded-xl p-3 space-y-2 font-mono text-xs">
      <h4 className="text-[11px] font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
        <span>Pinned Operational Alerts ({pinnedItems.length})</span>
      </h4>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {pinnedItems.map((item) => (
          <div
            key={item.notification_id}
            onClick={() => onSelectNotification?.(item)}
            className="p-2 bg-slate-900 border border-amber-700/50 rounded-lg min-w-[200px] max-w-[240px] cursor-pointer hover:border-amber-500 transition-all flex flex-col justify-between"
          >
            <div className="flex justify-between items-start">
              <span className="font-semibold text-slate-200 text-[11px] line-clamp-1">{item.title}</span>
              {onUnpin && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onUnpin(item.notification_id);
                  }}
                  className="text-amber-400 hover:text-white text-xs leading-none"
                >
                  &times;
                </button>
              )}
            </div>

            <div className="flex justify-between items-center text-[9px] text-slate-400 mt-2">
              <span className="text-amber-300 font-bold">{item.priority}</span>
              <span>{new Date(item.created_at).toLocaleTimeString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
