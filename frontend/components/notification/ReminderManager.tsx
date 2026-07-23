import React from "react";

export interface ReminderRecordDTO {
  reminder_id: string;
  notification_id: string;
  recipient_id: string;
  reminder_count: number;
  scheduled_at: string;
  status: string;
}

interface ReminderManagerProps {
  reminders: ReminderRecordDTO[];
  onScheduleReminder?: (notificationId: string) => Promise<void>;
  onRefresh?: () => void;
}

export const ReminderManager: React.FC<ReminderManagerProps> = ({
  reminders,
  onScheduleReminder,
  onRefresh,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 font-mono text-xs shadow-xl">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <span>Escalating Reminder Schedule</span>
            <span className="px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 text-[10px]">
              {reminders?.length || 0} Active
            </span>
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Manages escalating intervals ($2^n \times \text{base}$). Reminders suppress automatically upon acknowledgement.
          </p>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 text-xs"
          >
            Refresh
          </button>
        )}
      </div>

      {!reminders || reminders.length === 0 ? (
        <div className="text-xs text-slate-500 py-6 text-center bg-slate-950/40 rounded-lg border border-slate-800 italic">
          No active reminder schedules pending.
        </div>
      ) : (
        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
          {reminders.map((rem) => (
            <div
              key={rem.reminder_id}
              className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg flex justify-between items-center"
            >
              <div className="space-y-1">
                <div className="font-semibold text-slate-200">
                  Notification: <span className="text-purple-400">{rem.notification_id}</span>
                </div>
                <div className="text-[10px] text-slate-400">
                  Recipient: {rem.recipient_id} | Escalation Count: {rem.reminder_count}
                </div>
              </div>

              <div className="text-right font-mono space-y-1">
                <span className="px-2 py-0.5 bg-purple-950 text-purple-300 border border-purple-800 rounded text-[10px]">
                  {rem.status}
                </span>
                <div className="text-[9px] text-slate-500">{new Date(rem.scheduled_at).toLocaleTimeString()}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
