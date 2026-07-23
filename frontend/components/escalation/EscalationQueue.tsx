import React, { useState } from "react";
import { EscalationBadge } from "./EscalationBadge";

export interface EscalationQueueItemDTO {
  escalation_id: string;
  approval_id: string;
  reason: string;
  status: string;
  assigned_to_role: string;
  assigned_to_user?: string | null;
  created_at: string;
  version: number;
}

interface EscalationQueueProps {
  escalations: EscalationQueueItemDTO[];
  onSelectEscalation?: (id: string) => void;
  onAcknowledge?: (id: string) => void;
  onResolve?: (id: string) => void;
  onRefresh?: () => void;
}

export const EscalationQueue: React.FC<EscalationQueueProps> = ({
  escalations,
  onSelectEscalation,
  onAcknowledge,
  onResolve,
  onRefresh,
}) => {
  const [filterReason, setFilterReason] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filtered = (escalations || []).filter((item) => {
    if (filterReason !== "ALL" && item.reason !== filterReason) return false;
    if (filterStatus !== "ALL" && item.status !== filterStatus) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchReason = item.reason.toLowerCase().includes(q);
      const matchAppId = item.approval_id.toLowerCase().includes(q);
      const matchEscId = item.escalation_id.toLowerCase().includes(q);
      if (!matchReason && !matchAppId && !matchEscId) return false;
    }
    return true;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
      {/* Header controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>SLA Escalation & Command Queue</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
              {filtered.length} Active Escalations
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Acknowledge, reassign, or resolve active SLA timeout escalations and operational policy breaches.
          </p>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 transition-all"
          >
            Refresh Escalations
          </button>
        )}
      </div>

      {/* Filter controls */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
        <input
          type="text"
          placeholder="Search by ID or reason..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-rose-500"
        />

        <select
          value={filterReason}
          onChange={(e) => setFilterReason(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-rose-500"
        >
          <option value="ALL">All Escalation Reasons</option>
          <option value="SLA_TIMEOUT">SLA Timeout</option>
          <option value="OFFICER_UNAVAILABLE">Officer Unavailable</option>
          <option value="SUPERVISOR_UNAVAILABLE">Supervisor Unavailable</option>
          <option value="MANUAL_ESCALATION">Manual Escalation</option>
          <option value="EMERGENCY">Emergency</option>
          <option value="JURISDICTION_CONFLICT">Jurisdiction Conflict</option>
          <option value="POLICY_VIOLATION">Policy Violation</option>
        </select>

        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-rose-500"
        >
          <option value="ALL">All Statuses</option>
          <option value="PENDING">PENDING</option>
          <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
          <option value="RESOLVED">RESOLVED</option>
          <option value="EXPIRED">EXPIRED</option>
        </select>
      </div>

      {/* Escalation items */}
      {filtered.length === 0 ? (
        <div className="text-xs text-slate-500 py-8 text-center bg-slate-950/40 rounded-lg border border-slate-800">
          No escalations match current filter criteria.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
          {filtered.map((item) => (
            <div
              key={item.escalation_id}
              className="p-3.5 bg-slate-950/80 hover:bg-slate-950 border border-slate-800 hover:border-rose-800/80 rounded-lg text-xs transition-all space-y-2 font-mono"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-rose-400">{item.reason}</span>
                  <span className="text-[10px] text-slate-500">ID: {item.escalation_id}</span>
                </div>
                <EscalationBadge status={item.status} size="sm" />
              </div>

              <div className="flex justify-between items-center text-[11px] text-slate-300">
                <span>Approval: <strong className="text-cyan-400">{item.approval_id}</strong></span>
                <span>Role Queue: <strong className="text-purple-300">{item.assigned_to_role.toUpperCase()}</strong></span>
                <span>User: <strong className="text-slate-300">{item.assigned_to_user || "Unassigned"}</strong></span>
              </div>

              <div className="flex justify-between items-center pt-2 border-t border-slate-900">
                <span className="text-[10px] text-slate-500">Logged: {new Date(item.created_at).toLocaleString()}</span>
                <div className="flex gap-2">
                  {onAcknowledge && item.status === "PENDING" && (
                    <button
                      onClick={() => onAcknowledge(item.escalation_id)}
                      className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded text-[11px] font-medium"
                    >
                      Acknowledge
                    </button>
                  )}
                  {onResolve && item.status !== "RESOLVED" && (
                    <button
                      onClick={() => onResolve(item.escalation_id)}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-medium"
                    >
                      Resolve Escalation
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
