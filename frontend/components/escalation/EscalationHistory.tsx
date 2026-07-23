import React from "react";

export interface EscalationEventDTO {
  event_id: string;
  escalation_id: string;
  approval_id: string;
  reason: string;
  from_role: string;
  to_role: string;
  from_user?: string | null;
  to_user?: string | null;
  details?: Record<string, any>;
  timestamp: string;
}

interface EscalationHistoryProps {
  events: EscalationEventDTO[];
}

export const EscalationHistory: React.FC<EscalationHistoryProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return <div className="text-xs text-slate-500 py-4 text-center">No escalation history recorded.</div>;
  }

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
        Escalation Audit Trail ({events.length} Event{events.length > 1 ? "s" : ""})
      </h4>

      <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1 font-mono text-xs">
        {events.map((evt) => (
          <div key={evt.event_id} className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 bg-rose-950 text-rose-300 border border-rose-800 rounded font-semibold text-[10px]">
                {evt.reason}
              </span>
              <span className="text-[10px] text-slate-500">{new Date(evt.timestamp).toLocaleTimeString()}</span>
            </div>

            <div className="flex items-center gap-2 text-[11px] text-slate-300">
              <span>Authority Route:</span>
              <span className="text-slate-400">{evt.from_role.toUpperCase()}</span>
              <span>&rarr;</span>
              <span className="text-cyan-400 font-bold">{evt.to_role.toUpperCase()}</span>
            </div>

            {(evt.from_user || evt.to_user) && (
              <div className="text-[10px] text-slate-400">
                User: {evt.from_user || "System"} &rarr; {evt.to_user || "Role Queue"}
              </div>
            )}

            {evt.details && Object.keys(evt.details).length > 0 && (
              <pre className="text-[10px] bg-slate-900 p-2 rounded border border-slate-800 text-slate-400 overflow-x-auto">
                {JSON.stringify(evt.details, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
