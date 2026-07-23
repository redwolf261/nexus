import React, { useState } from "react";
import { ApprovalStatusChip } from "./ApprovalStatusChip";
import { ApprovalTimeline, ApprovalStageDTO } from "./ApprovalTimeline";
import { ApprovalHistory, ApprovalHistoryDTO } from "./ApprovalHistory";

export interface ApprovalDetailDTO {
  approval_id: string;
  title: string;
  description: string;
  approval_type: string;
  entity_type: string;
  entity_id: string;
  requester_id: string;
  requester_role: string;
  district_id: string;
  status: string;
  stages: ApprovalStageDTO[];
  current_stage_index: number;
  history: ApprovalHistoryDTO[];
  created_at: string;
  expires_at?: string | null;
  metadata?: Record<string, any>;
  version: number;
}

interface ApprovalReviewProps {
  approval: ApprovalDetailDTO;
  onOpenDecisionDialog?: () => void;
}

export const ApprovalReview: React.FC<ApprovalReviewProps> = ({
  approval,
  onOpenDecisionDialog,
}) => {
  const [activeTab, setActiveTab] = useState<"timeline" | "history" | "metadata">("timeline");

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
      {/* Header section */}
      <div className="flex justify-between items-start border-b border-slate-800 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-slate-100">{approval.title}</h2>
            <ApprovalStatusChip status={approval.status} size="md" />
          </div>
          <p className="text-xs text-slate-400">{approval.description || "No description provided."}</p>
        </div>

        {onOpenDecisionDialog && approval.status === "UNDER_REVIEW" && (
          <button
            onClick={onOpenDecisionDialog}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium text-xs rounded-lg shadow-lg shadow-purple-950/50 transition-all flex items-center gap-1.5"
          >
            Review & Submit Decision
          </button>
        )}
      </div>

      {/* Grid Specs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-800 font-mono">
        <div>
          <span className="text-slate-500 block text-[10px]">APPROVAL TYPE</span>
          <span className="text-cyan-400 font-semibold">{approval.approval_type}</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px]">REQUESTER</span>
          <span className="text-slate-200 font-semibold">{approval.requester_id}</span>
          <span className="text-slate-400 text-[10px] block">({approval.requester_role})</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px]">TARGET ENTITY</span>
          <span className="text-slate-200">{approval.entity_type}</span>
          <span className="text-slate-400 text-[10px] block">ID: {approval.entity_id}</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px]">DISTRICT & EXPIRY</span>
          <span className="text-slate-200">{approval.district_id}</span>
          <span className="text-amber-400 text-[10px] block">
            {approval.expires_at ? new Date(approval.expires_at).toLocaleDateString() : "No Expiry"}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 text-xs font-semibold">
        {(["timeline", "history", "metadata"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 capitalize transition-all border-b-2 ${
              activeTab === tab
                ? "border-cyan-500 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      <div className="pt-2">
        {activeTab === "timeline" && (
          <ApprovalTimeline
            stages={approval.stages}
            currentStageIndex={approval.current_stage_index}
            overallStatus={approval.status}
          />
        )}

        {activeTab === "history" && <ApprovalHistory history={approval.history} />}

        {activeTab === "metadata" && (
          <pre className="text-xs bg-slate-950 p-4 rounded-lg border border-slate-800 text-slate-300 font-mono overflow-x-auto">
            {JSON.stringify(approval.metadata || {}, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};
