import React from "react";
import { NotificationCard, NotificationDTO } from "./NotificationCard";

export interface ThreadDTO {
  thread_id: string;
  entity_type: string;
  entity_id: string;
  title: string;
  total_count: number;
  unread_count: number;
  latest_event_type: string;
  updated_at: string;
  notifications: NotificationDTO[];
}

interface ThreadViewProps {
  thread: ThreadDTO | null;
  onAcknowledge?: (id: string) => void;
  onDismiss?: (id: string) => void;
}

export const ThreadView: React.FC<ThreadViewProps> = ({ thread, onAcknowledge, onDismiss }) => {
  if (!thread) {
    return (
      <div className="text-xs text-slate-500 py-8 text-center bg-slate-950/40 rounded-lg border border-slate-800 font-mono">
        Select a notification thread to view grouped conversation history.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 font-mono text-xs shadow-xl">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <span>Thread: {thread.entity_type} {thread.entity_id}</span>
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px]">
              {thread.total_count} Events
            </span>
          </h3>
          <p className="text-[10px] text-slate-400 mt-0.5">{thread.title}</p>
        </div>

        <span className="text-[10px] text-slate-500">Updated: {new Date(thread.updated_at).toLocaleTimeString()}</span>
      </div>

      <div className="space-y-2.5 max-h-[400px] overflow-y-auto pr-1">
        {thread.notifications.map((item) => (
          <NotificationCard
            key={item.notification_id}
            notification={item}
            onAcknowledge={onAcknowledge}
            onDismiss={onDismiss}
          />
        ))}
      </div>
    </div>
  );
};
