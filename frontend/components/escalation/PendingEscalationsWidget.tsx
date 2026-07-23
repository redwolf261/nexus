import React from "react";
import { EscalationBadge } from "./EscalationBadge";

export interface PendingEscalationSummaryDTO {
  escalation_id: string;
  approval_id: string;
  reason: string;
  status: string;
  assigned_to_role: string;
  created_at: string;
}

interface PendingEscalationsWidgetProps {
  escalations: PendingEscalationSummaryDTO[];
  onSelectEscalation?: (id: string) => void;
}

export const PendingEscalationsWidget: React.FC<PendingEscalationsWidgetProps> = ({
  escalations,
  onSelectEscalation,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 shadow-xl">
      <div className="flex justify-between items-center">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span>Active Command Escalations</span>
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
        </h3>
        <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono text-xs font-bold">
          {escalations?.length || 0} Critical
        </span>
      </div>

      {!escalations || escalations.length === 0 ? (
        <div className="text-xs text-slate-500 py-6 text-center italic">
          Zero active escalations requiring supervisor intervention.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
          {escalations.map((item) => (
            <div
              key={item.escalation_id}
              onClick={() => onSelectEscalation?.(item.escalation_id)}
              className="p-3 bg-slate-950/80 border border-slate-800 hover:border-rose-800/80 rounded-lg text-xs cursor-pointer transition-all hover:shadow-md space-y-1.5 font-mono"
            >
              <div className="flex justify-between items-center">
                <span className="font-bold text-rose-400">{item.reason}</span>
                <EscalationBadge status={item.status} size="sm" />
              </div>

              <div className="text-slate-300">
                Approval ID: <span className="text-cyan-400">{item.approval_id}</span>
              </div>

              <div className="flex justify-between items-center text-[10px] text-slate-500 pt-1 border-t border-slate-900">
                <span>Assigned Tier: {item.assigned_to_role.toUpperCase()}</span>
                <span>{new Date(item.created_at).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
