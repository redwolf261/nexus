import React from "react";
import { ApprovalStatusChip } from "./ApprovalStatusChip";

export interface PendingSummaryDTO {
  approval_id: string;
  title: string;
  approval_type: string;
  requester_id: string;
  district_id: string;
  created_at: string;
  required_role: string;
}

interface PendingApprovalsWidgetProps {
  pendingItems: PendingSummaryDTO[];
  onSelectApproval?: (id: string) => void;
}

export const PendingApprovalsWidget: React.FC<PendingApprovalsWidgetProps> = ({
  pendingItems,
  onSelectApproval,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 shadow-lg">
      <div className="flex justify-between items-center">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span>Pending Governance Approvals</span>
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
        </h3>
        <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono text-xs font-bold">
          {pendingItems?.length || 0} Require Action
        </span>
      </div>

      {!pendingItems || pendingItems.length === 0 ? (
        <div className="text-xs text-slate-500 py-6 text-center italic">
          Zero pending approvals awaiting your review.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
          {pendingItems.map((item) => (
            <div
              key={item.approval_id}
              onClick={() => onSelectApproval?.(item.approval_id)}
              className="p-3 bg-slate-950/80 border border-slate-800 hover:border-purple-800/80 rounded-lg text-xs cursor-pointer transition-all hover:shadow-md space-y-1.5"
            >
              <div className="flex justify-between items-start">
                <span className="font-semibold text-slate-200 line-clamp-1">{item.title}</span>
                <ApprovalStatusChip status="UNDER_REVIEW" size="sm" />
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span className="text-cyan-400 font-medium">{item.approval_type}</span>
                <span>By: {item.requester_id}</span>
              </div>

              <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-900">
                <span>Role Tier: {item.required_role.toUpperCase()}</span>
                <span>{new Date(item.created_at).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
