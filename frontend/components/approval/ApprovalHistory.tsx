import React from "react";

export interface ApprovalHistoryDTO {
  history_id: string;
  approval_id: string;
  action: string;
  previous_state: string;
  new_state: string;
  actor_id: string;
  actor_role: string;
  details?: Record<string, any>;
  timestamp: string;
}

interface ApprovalHistoryProps {
  history: ApprovalHistoryDTO[];
}

export const ApprovalHistory: React.FC<ApprovalHistoryProps> = ({ history }) => {
  if (!history || history.length === 0) {
    return <div className="text-xs text-slate-500 py-4 text-center">No history logs recorded.</div>;
  }

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
        Immutable Audit History Trail ({history.length} Log{history.length > 1 ? "s" : ""})
      </h4>

      <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
        {history.map((log) => (
          <div
            key={log.history_id}
            className="p-3 bg-slate-900/90 border border-slate-800 rounded-lg text-xs space-y-1.5 font-mono"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-slate-800 text-cyan-300 rounded font-semibold text-[11px] border border-slate-700">
                  {log.action}
                </span>
                <span className="text-slate-400">
                  by <strong className="text-slate-200">{log.actor_id}</strong> ({log.actor_role})
                </span>
              </div>
              <span className="text-[10px] text-slate-500">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
            </div>

            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              <span>Transition:</span>
              <span className="text-amber-400">{log.previous_state}</span>
              <span>&rarr;</span>
              <span className="text-emerald-400">{log.new_state}</span>
            </div>

            {log.details && Object.keys(log.details).length > 0 && (
              <pre className="text-[10px] bg-slate-950 p-2 rounded border border-slate-800/80 text-slate-400 overflow-x-auto">
                {JSON.stringify(log.details, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
