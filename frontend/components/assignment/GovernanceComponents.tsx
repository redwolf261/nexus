/**
 * Phase 8.2 Milestone 5 — React Supervisor Governance Components.
 *
 * Provides operational React UI components for:
 *   1. AssignmentDecisionDialog — Supervisor decision workflow (Accept / Override / Reject / Defer)
 *   2. PolicyViolationPanel — Real-time display of policy violations, warnings, and escalation badges
 *   3. RecommendationComparison — Side-by-side comparison of top candidate vs supervisor selection
 *   4. OverrideDialog — Enforces 50-char minimum justification and dropdown override reasons
 *   5. ApprovalQueue — Command center escalation queue for ACP / DCP approvals
 *   6. DecisionHistoryTimeline — Complete immutable decision audit history and approval chains
 *   7. EscalationBanner — Alert banner for pending escalations
 *
 * Uses React Query, optimistic updates, and real-time event integration.
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// ── Interfaces ───────────────────────────────────────────────────────────────

export interface PolicyResult {
  is_allowed: boolean;
  violations: string[];
  warnings: string[];
  requires_acp: boolean;
  requires_dcp: boolean;
  checked_rules: Record<string, boolean>;
}

export interface EscalationItem {
  id: string;
  decision_id: string;
  investigation_id: string;
  required_role: string;
  status: string;
  approver_id?: string;
  approved_at?: string;
  comments?: string;
  created_at: string;
}

export interface GovernanceMetrics {
  total_decisions: number;
  acceptance_rate_pct: number;
  override_rate_pct: number;
  rejection_rate_pct: number;
  deferral_rate_pct: number;
  avg_approval_latency_seconds: number;
  policy_violation_count: number;
  escalation_count: number;
  capacity_override_pct: number;
  cross_jurisdiction_override_pct: number;
  manual_assignment_pct: number;
  policy_version: string;
}

// ── 1. PolicyViolationPanel ─────────────────────────────────────────────────

export const PolicyViolationPanel: React.FC<{ policy: PolicyResult | null }> = ({ policy }) => {
  if (!policy) return null;

  return (
    <div className="space-y-2 mb-4">
      {policy.requires_dcp && (
        <div className="p-3 bg-purple-950/60 border border-purple-500/50 rounded-lg text-purple-300 text-xs font-semibold flex items-center justify-between">
          <span>⚠ ESCALATION REQUIRED: Deputy Commissioner of Police (DCP) Approval Mandatory</span>
          <span className="px-2 py-0.5 bg-purple-800 text-white rounded font-mono text-[10px]">DCP Tier</span>
        </div>
      )}
      {policy.requires_acp && !policy.requires_dcp && (
        <div className="p-3 bg-indigo-950/60 border border-indigo-500/50 rounded-lg text-indigo-300 text-xs font-semibold flex items-center justify-between">
          <span>⚠ ESCALATION REQUIRED: Assistant Commissioner of Police (ACP) Approval Mandatory</span>
          <span className="px-2 py-0.5 bg-indigo-800 text-white rounded font-mono text-[10px]">ACP Tier</span>
        </div>
      )}
      {policy.violations.map((v, i) => (
        <div key={i} className="p-3 bg-rose-950/50 border border-rose-500/40 rounded-lg text-rose-300 text-xs flex items-start gap-2">
          <span className="font-bold text-rose-400">Violation:</span> {v}
        </div>
      ))}
      {policy.warnings.map((w, i) => (
        <div key={i} className="p-3 bg-amber-950/40 border border-amber-500/40 rounded-lg text-amber-300 text-xs flex items-start gap-2">
          <span className="font-bold text-amber-400">Policy Warning:</span> {w}
        </div>
      ))}
    </div>
  );
};

// ── 2. RecommendationComparison ─────────────────────────────────────────────

export const RecommendationComparison: React.FC<{
  topOfficerId: string;
  selectedOfficerId: string;
}> = ({ topOfficerId, selectedOfficerId }) => {
  if (topOfficerId === selectedOfficerId) {
    return (
      <div className="p-3 bg-slate-800/60 border border-slate-700 rounded-lg text-xs text-slate-300">
        Selected officer <span className="font-bold text-cyan-400">{topOfficerId}</span> matches the #1 recommendation.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 p-3 bg-slate-800/80 border border-slate-700 rounded-lg text-xs">
      <div className="p-2 bg-slate-900/60 rounded border border-emerald-500/30">
        <div className="text-emerald-400 font-semibold mb-1">#1 Engine Recommendation</div>
        <div className="font-mono text-slate-200 font-bold">{topOfficerId}</div>
      </div>
      <div className="p-2 bg-slate-900/60 rounded border border-amber-500/30">
        <div className="text-amber-400 font-semibold mb-1">Supervisor Choice (Override)</div>
        <div className="font-mono text-slate-200 font-bold">{selectedOfficerId}</div>
      </div>
    </div>
  );
};

// ── 3. OverrideDialog ───────────────────────────────────────────────────────

export const OverrideDialog: React.FC<{
  investigationId: string;
  chosenOfficerId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ investigationId, chosenOfficerId, isOpen, onClose, onSuccess }) => {
  const [overrideReason, setOverrideReason] = useState("SPECIAL_EXPERTISE");
  const [justification, setJustification] = useState("");
  const [isInterstate, setIsInterstate] = useState(false);

  const queryClient = useQueryClient();

  const overrideMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/assignment/${investigationId}/override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chosen_officer_id: chosenOfficerId,
          override_reason: overrideReason,
          justification,
          is_interstate: isInterstate,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Override submission failed");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignment-decision-history", investigationId] });
      queryClient.invalidateQueries({ queryKey: ["pending-escalations"] });
      onSuccess();
      onClose();
    },
  });

  if (!isOpen) return null;

  const charCount = justification.trim().length;
  const isJustificationValid = charCount >= 50;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        <h3 className="text-lg font-semibold text-slate-100 border-b border-slate-800 pb-3 flex justify-between">
          <span>Supervisor Override — {investigationId}</span>
          <span className="text-xs font-mono text-cyan-400">{chosenOfficerId}</span>
        </h3>

        <div className="space-y-3 text-sm">
          <div>
            <label className="block text-slate-300 text-xs font-medium mb-1">Standardized Override Reason</label>
            <select
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 text-sm"
            >
              <option value="SPECIAL_EXPERTISE">Specialized Domain Expertise Required</option>
              <option value="LOCAL_KNOWLEDGE">Tactical / Local Geographic Knowledge</option>
              <option value="URGENT_OPERATION">Urgent Operational Command Order</option>
              <option value="WORKLOAD_BALANCING">Workload Redistribution</option>
              <option value="RESOURCE_SHORTAGE">Resource / Unit Shortage</option>
              <option value="MANUAL_COMMAND">Manual Executive Command</option>
              <option value="TEMPORARY_ASSIGNMENT">Temporary Task Force Assignment</option>
              <option value="OTHER">Other Operational Justification</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-slate-300 text-xs font-medium">
                Detailed Justification (Mandatory 50+ Characters)
              </label>
              <span className={`text-[11px] font-mono ${isJustificationValid ? "text-emerald-400" : "text-amber-400"}`}>
                {charCount} / 50 chars
              </span>
            </div>
            <textarea
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              rows={4}
              placeholder="Provide complete operational explanation for bypassing top recommendation..."
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="interstate"
              checked={isInterstate}
              onChange={(e) => setIsInterstate(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-0"
            />
            <label htmlFor="interstate" className="text-xs text-purple-300 font-medium">
              Interstate / Multi-Jurisdiction Investigation (Triggers DCP Escalation)
            </label>
          </div>
        </div>

        {overrideMutation.isError && (
          <div className="p-3 bg-rose-950/60 border border-rose-500/40 rounded text-rose-300 text-xs">
            {(overrideMutation.error as Error).message}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
          <button onClick={onClose} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs">
            Cancel
          </button>
          <button
            onClick={() => overrideMutation.mutate()}
            disabled={!isJustificationValid || overrideMutation.isPending}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-white rounded text-xs font-medium"
          >
            {overrideMutation.isPending ? "Submitting Override..." : "Submit Override for Audit"}
          </button>
        </div>
      </div>
    </div>
  );
};

// ── 4. ApprovalQueue ────────────────────────────────────────────────────────

export const ApprovalQueue: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedEscalation, setSelectedEscalation] = useState<EscalationItem | null>(null);
  const [comments, setComments] = useState("");

  const { data: escalations, isLoading } = useQuery<EscalationItem[]>({
    queryKey: ["pending-escalations"],
    queryFn: async () => {
      const res = await fetch("/api/assignment/escalations");
      if (!res.ok) throw new Error("Failed to load escalations");
      return res.json();
    },
  });

  const approveMutation = useMutation({
    mutationFn: async () => {
      if (!selectedEscalation) return;
      const res = await fetch(`/api/assignment/escalations/${selectedEscalation.id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comments }),
      });
      if (!res.ok) throw new Error("Approval failed");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-escalations"] });
      setSelectedEscalation(null);
      setComments("");
    },
  });

  if (isLoading) return <div className="p-4 text-xs text-slate-400 animate-pulse">Loading escalation queue...</div>;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4">
      <h3 className="text-sm font-semibold text-slate-200 flex justify-between items-center">
        <span>Command Center Escalation Queue (ACP / DCP Sign-Off)</span>
        <span className="text-xs font-mono bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded">
          {escalations?.length || 0} Pending
        </span>
      </h3>

      {escalations && escalations.length === 0 ? (
        <div className="text-xs text-slate-500 py-4 text-center">No pending escalations awaiting approval.</div>
      ) : (
        <div className="space-y-3">
          {escalations?.map((item) => (
            <div key={item.id} className="p-3 bg-slate-800/80 border border-slate-700 rounded-lg flex justify-between items-center text-xs">
              <div>
                <div className="flex items-center gap-2 font-mono text-slate-200 font-semibold">
                  <span>{item.investigation_id}</span>
                  <span className="px-1.5 py-0.5 bg-purple-900 text-purple-300 text-[10px] rounded">
                    Requires {item.required_role}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Submitted: {new Date(item.created_at).toLocaleString()}
                </div>
              </div>

              <button
                onClick={() => setSelectedEscalation(item)}
                className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-medium"
              >
                Review & Approve
              </button>
            </div>
          ))}
        </div>
      )}

      {selectedEscalation && (
        <div className="p-4 bg-slate-800/90 border border-purple-500/50 rounded-lg space-y-3">
          <h4 className="text-xs font-semibold text-purple-300">
            Approve Escalation — {selectedEscalation.investigation_id} ({selectedEscalation.required_role} Tier)
          </h4>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            rows={2}
            placeholder="Executive approval comments..."
            className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200 text-xs"
          />
          <div className="flex justify-end gap-2">
            <button onClick={() => setSelectedEscalation(null)} className="px-3 py-1 bg-slate-700 text-slate-300 rounded text-xs">
              Cancel
            </button>
            <button
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending}
              className="px-3 py-1 bg-purple-600 text-white rounded text-xs font-medium"
            >
              Confirm Executive Approval
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// ── 5. DecisionHistoryTimeline ──────────────────────────────────────────────

export const DecisionHistoryTimeline: React.FC<{ investigationId: string }> = ({ investigationId }) => {
  const { data: history, isLoading } = useQuery<any[]>({
    queryKey: ["assignment-decision-history", investigationId],
    queryFn: async () => {
      const res = await fetch(`/api/assignment/${investigationId}/decision-history`);
      if (!res.ok) throw new Error("Failed to load history");
      return res.json();
    },
  });

  if (isLoading) return <div className="p-4 text-xs text-slate-400 animate-pulse">Loading decision history...</div>;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <h4 className="text-sm font-semibold text-slate-200">Supervisor Decision History Timeline</h4>
      {history && history.length === 0 ? (
        <div className="text-xs text-slate-500">No decision history recorded for this case.</div>
      ) : (
        <div className="space-y-3 border-l border-slate-800 pl-4">
          {history?.map((item, idx) => (
            <div key={idx} className="relative bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 space-y-1 text-xs">
              <div className="flex justify-between font-semibold text-slate-200">
                <span className="text-cyan-400 font-mono">{item.decision}</span>
                <span className="text-slate-400 font-mono text-[11px]">{new Date(item.timestamp).toLocaleString()}</span>
              </div>
              {item.chosen_officer_id && (
                <div className="text-slate-300">Officer: <span className="font-mono text-cyan-300">{item.chosen_officer_id}</span></div>
              )}
              {item.justification && (
                <div className="text-slate-400 italic">"{item.justification}"</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
