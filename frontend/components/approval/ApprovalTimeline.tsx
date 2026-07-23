import React from "react";
import { ApprovalStatusChip } from "./ApprovalStatusChip";

export interface ApprovalStageDTO {
  stage_id: string;
  stage_order: number;
  stage_name: string;
  required_role: string;
  min_approvers: number;
  approvers: string[];
  status: string;
  approved_by: string[];
  rejected_by?: string | null;
  comments?: string | null;
  completed_at?: string | null;
}

interface ApprovalTimelineProps {
  stages: ApprovalStageDTO[];
  currentStageIndex: number;
  overallStatus: string;
}

export const ApprovalTimeline: React.FC<ApprovalTimelineProps> = ({
  stages,
  currentStageIndex,
  overallStatus,
}) => {
  if (!stages || stages.length === 0) {
    return <div className="text-xs text-slate-500 py-2">No stages defined for workflow.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Approval Workflow Pipeline ({stages.length} Stage{stages.length > 1 ? "s" : ""})
        </h4>
        <ApprovalStatusChip status={overallStatus} size="sm" />
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {stages.map((stg, idx) => {
          const isCurrent = idx === currentStageIndex && overallStatus === "UNDER_REVIEW";
          const isCompleted = stg.status === "APPROVED";
          const isRejected = stg.status === "REJECTED";
          const isEscalated = stg.status === "ESCALATED";

          let dotColor = "bg-slate-800 border-slate-700 text-slate-400";
          if (isCompleted) {
            dotColor = "bg-emerald-600 border-emerald-500 text-white";
          } else if (isRejected) {
            dotColor = "bg-rose-600 border-rose-500 text-white";
          } else if (isEscalated) {
            dotColor = "bg-purple-600 border-purple-500 text-white";
          } else if (isCurrent) {
            dotColor = "bg-amber-500 border-amber-400 text-slate-950 animate-pulse";
          }

          return (
            <div key={stg.stage_id} className="relative group">
              <span
                className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full border flex items-center justify-center text-[10px] font-bold font-mono ${dotColor}`}
              >
                {stg.stage_order}
              </span>

              <div
                className={`p-3 rounded-lg border text-xs transition-all ${
                  isCurrent
                    ? "bg-amber-950/20 border-amber-800/60 shadow-lg shadow-amber-950/20"
                    : isCompleted
                    ? "bg-slate-900/80 border-emerald-900/40"
                    : "bg-slate-900/40 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-slate-200">{stg.stage_name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    Required: {stg.required_role.toUpperCase()}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono mt-2">
                  <span>
                    Approved: {stg.approved_by?.length || 0} / {stg.min_approvers} Min
                  </span>
                  <span className="uppercase text-[10px] font-bold">
                    {stg.status}
                  </span>
                </div>

                {stg.approved_by && stg.approved_by.length > 0 && (
                  <div className="mt-2 text-[11px] text-emerald-400 flex items-center gap-1">
                    <span className="font-semibold">Signatures:</span>
                    <span className="font-mono text-slate-300">{stg.approved_by.join(", ")}</span>
                  </div>
                )}

                {stg.comments && (
                  <div className="mt-2 p-2 rounded bg-slate-950/60 border border-slate-800 text-[11px] text-slate-300 italic">
                    "{stg.comments}"
                  </div>
                )}

                {stg.completed_at && (
                  <div className="mt-1 text-[10px] text-slate-500 font-mono text-right">
                    Completed: {new Date(stg.completed_at).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
