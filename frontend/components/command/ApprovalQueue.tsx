import React from "react";

export interface ApprovalItem {
  approval_id: string;
  investigation_id: string;
  decision_type: string;
  chosen_officer_id?: string;
  supervisor_id: string;
  required_role: string;
  override_reason?: string;
  justification?: string;
  status: string;
  created_at: string;
}

export const ApprovalQueue: React.FC<{ approvals?: ApprovalItem[]; onApprove?: (id: string) => void }> = ({
  approvals,
  onApprove,
}) => {
  if (!approvals || approvals.length === 0) {
    return <div className="text-xs text-slate-500 py-4 text-center">No pending approvals in queue.</div>;
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-semibold text-slate-200 flex justify-between items-center">
        <span>Pending Operational Approvals</span>
        <span className="text-xs font-mono bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded">
          {approvals.length} Pending
        </span>
      </h3>

      <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
        {approvals.map((item) => (
          <div key={item.approval_id} className="p-3 bg-slate-800/80 border border-slate-700 rounded-lg space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <div className="font-mono text-slate-200 font-bold flex items-center gap-2">
                <span>{item.investigation_id}</span>
                <span className="px-1.5 py-0.5 bg-purple-900 text-purple-300 text-[10px] rounded font-semibold">
                  {item.required_role} Tier
                </span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">{new Date(item.created_at).toLocaleTimeString()}</span>
            </div>

            <div className="text-slate-300">
              Type: <span className="font-semibold text-cyan-400">{item.decision_type}</span> | Candidate: <span className="font-mono text-slate-200">{item.chosen_officer_id || "N/A"}</span>
            </div>

            {item.override_reason && (
              <div className="text-[11px] text-amber-400 font-medium">Reason: {item.override_reason}</div>
            )}
            {item.justification && (
              <div className="text-[11px] text-slate-400 italic bg-slate-900/60 p-2 rounded border border-slate-800">
                "{item.justification}"
              </div>
            )}

            {onApprove && (
              <div className="flex justify-end pt-1">
                <button
                  onClick={() => onApprove(item.approval_id)}
                  className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-medium"
                >
                  Approve Request
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
