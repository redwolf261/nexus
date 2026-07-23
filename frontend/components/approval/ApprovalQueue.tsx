import React, { useState } from "react";
import { ApprovalStatusChip } from "./ApprovalStatusChip";

export interface ApprovalQueueItemDTO {
  approval_id: string;
  title: string;
  approval_type: string;
  entity_type: string;
  entity_id: string;
  requester_id: string;
  district_id: string;
  status: string;
  created_at: string;
  version: number;
}

interface ApprovalQueueProps {
  approvals: ApprovalQueueItemDTO[];
  onSelectApproval?: (id: string) => void;
  onRefresh?: () => void;
}

export const ApprovalQueue: React.FC<ApprovalQueueProps> = ({
  approvals,
  onSelectApproval,
  onRefresh,
}) => {
  const [filterType, setFilterType] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filtered = (approvals || []).filter((item) => {
    if (filterType !== "ALL" && item.approval_type !== filterType) return false;
    if (filterStatus !== "ALL" && item.status !== filterStatus) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchReq = item.requester_id.toLowerCase().includes(q);
      const matchId = item.approval_id.toLowerCase().includes(q);
      if (!matchTitle && !matchReq && !matchId) return false;
    }
    return true;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
      {/* Header controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>Governance & Operational Approvals Queue</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
              {filtered.length} Total
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Inspect, approve, reject, or escalate operational warrant and resource authorization requests.
          </p>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 transition-all"
          >
            Refresh Queue
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <input
          type="text"
          placeholder="Search by title, requester, or approval ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500"
        />

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
        >
          <option value="ALL">All Approval Types</option>
          <option value="SEARCH_WARRANT">Search Warrant</option>
          <option value="ARREST_WARRANT">Arrest Warrant</option>
          <option value="EVIDENCE_COLLECTION">Evidence Collection</option>
          <option value="SURVEILLANCE_REQUEST">Surveillance Request</option>
          <option value="INVESTIGATION_CLOSURE">Investigation Closure</option>
          <option value="COLD_CASE_ARCHIVAL">Cold Case Archival</option>
          <option value="CASE_REOPENING">Case Reopening</option>
          <option value="CROSS_DISTRICT_INVESTIGATION">Cross District</option>
          <option value="BUDGET_RESOURCE_REQUEST">Budget/Resource</option>
          <option value="EMERGENCY_OPERATIONAL_APPROVAL">Emergency Approval</option>
        </select>

        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
        >
          <option value="ALL">All Statuses</option>
          <option value="UNDER_REVIEW">UNDER_REVIEW</option>
          <option value="APPROVED">APPROVED</option>
          <option value="REJECTED">REJECTED</option>
          <option value="RETURNED">RETURNED</option>
          <option value="ESCALATED">ESCALATED</option>
          <option value="EXPIRED">EXPIRED</option>
          <option value="CANCELLED">CANCELLED</option>
        </select>
      </div>

      {/* Table list */}
      {filtered.length === 0 ? (
        <div className="text-xs text-slate-500 py-8 text-center bg-slate-950/40 rounded-lg border border-slate-800">
          No approval requests match the current filters.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
          {filtered.map((item) => (
            <div
              key={item.approval_id}
              onClick={() => onSelectApproval?.(item.approval_id)}
              className="p-3.5 bg-slate-950/80 hover:bg-slate-950 border border-slate-800 hover:border-cyan-800/80 rounded-lg text-xs cursor-pointer transition-all flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-200">{item.title}</span>
                  <span className="font-mono text-[10px] text-slate-500">ID: {item.approval_id}</span>
                </div>

                <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
                  <span>Type: <strong className="text-cyan-400">{item.approval_type}</strong></span>
                  <span>Requester: <strong className="text-slate-300">{item.requester_id}</strong></span>
                  <span>District: <strong className="text-slate-300">{item.district_id}</strong></span>
                </div>
              </div>

              <div className="flex items-center gap-3 font-mono text-[11px]">
                <ApprovalStatusChip status={item.status} size="sm" />
                <span className="text-slate-500">{new Date(item.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
