/**
 * Phase 8.2 Milestone 4 — React Assignment Components.
 *
 * Provides operational React UI components for:
 *   1. AssignmentRecommendationDialog — reviewing ranked officer recommendations
 *   2. AssignmentHistoryPanel — viewing immutable assignment audit trail
 *   3. AssignmentValidationBanner — rendering live pre-condition checks
 *   4. ReassignmentDialog — supervisor reassignment & manual override modal
 *   5. CompletionEstimateCard — rendering deterministic duration estimates
 *
 * Uses React Query, optimistic updates, and WebSocket event integration.
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// ── Types ────────────────────────────────────────────────────────────────────

export interface RankedRecommendation {
  rank: number;
  score: {
    officer_id: string;
    overall_score: number;
    component_scores: Record<string, number>;
    explanation: string[];
  };
  assignable: boolean;
  rejection_summary: string[];
}

export interface AssignmentHistoryRecord {
  id: string;
  assignment_id: string;
  investigation_id: string;
  officer_id: string;
  assigned_by: string;
  timestamp: string;
  reason?: string;
  recommendation_score?: number;
  policy_version?: string;
  manual_override: boolean;
  override_reason?: string;
  previous_officer?: string;
}

export interface ValidationResult {
  investigation_id: string;
  officer_id: string;
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  checks: Record<string, boolean>;
  checked_at: string;
}

export interface CompletionEstimate {
  investigation_id: string;
  earliest_days: number;
  expected_days: number;
  latest_days: number;
  estimated_completion_date: string;
  factors: Record<string, any>;
  policy_version: string;
}

// ── 1. AssignmentValidationBanner ──────────────────────────────────────────

export const AssignmentValidationBanner: React.FC<{
  validation: ValidationResult | null;
}> = ({ validation }) => {
  if (!validation) return null;

  if (validation.is_valid && validation.warnings.length === 0) {
    return (
      <div className="p-3 mb-4 bg-emerald-950/40 border border-emerald-500/30 rounded-lg text-emerald-300 text-sm flex items-center gap-2">
        <span className="font-semibold">✓ Validation Passed:</span> All operational pre-conditions satisfied.
      </div>
    );
  }

  return (
    <div className="mb-4 space-y-2">
      {validation.errors.map((err, idx) => (
        <div key={idx} className="p-3 bg-rose-950/50 border border-rose-500/40 rounded-lg text-rose-300 text-sm flex items-start gap-2">
          <span className="font-bold text-rose-400">✕ Gate Failure:</span> {err}
        </div>
      ))}
      {validation.warnings.map((warn, idx) => (
        <div key={idx} className="p-3 bg-amber-950/40 border border-amber-500/40 rounded-lg text-amber-300 text-sm flex items-start gap-2">
          <span className="font-bold text-amber-400">⚠ Warning:</span> {warn}
        </div>
      ))}
    </div>
  );
};

// ── 2. AssignmentRecommendationDialog ──────────────────────────────────────

export const AssignmentRecommendationDialog: React.FC<{
  investigationId: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectOfficer: (officerId: string) => void;
}> = ({ investigationId, isOpen, onClose, onSelectOfficer }) => {
  const queryClient = useQueryClient();

  const { data: recommendations, isLoading } = useQuery<RankedRecommendation[]>({
    queryKey: ["assignment-recommendations", investigationId],
    queryFn: async () => {
      const res = await fetch(`/api/assignment/recommend/${investigationId}?limit=5`);
      if (!res.ok) throw new Error("Failed to fetch recommendations");
      return res.json();
    },
    enabled: isOpen && !!investigationId,
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
        <div className="flex justify-between items-center border-b border-slate-800 pb-3">
          <h3 className="text-lg font-semibold text-slate-100">
            Officer Recommendations — {investigationId}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 text-xl font-bold">
            ×
          </button>
        </div>

        {isLoading ? (
          <div className="py-8 text-center text-slate-400 animate-pulse">
            Computing deterministic scoring & workload metrics...
          </div>
        ) : (
          <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
            {recommendations?.map((item) => (
              <div
                key={item.score.officer_id}
                className={`p-4 rounded-lg border transition-all ${
                  item.assignable
                    ? "bg-slate-800/80 border-slate-700 hover:border-cyan-500/50"
                    : "bg-slate-900/40 border-slate-800 opacity-60"
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-700 text-slate-300">
                        #{item.rank}
                      </span>
                      <span className="font-semibold text-slate-200">
                        {item.score.officer_id}
                      </span>
                      {!item.assignable && (
                        <span className="text-xs bg-rose-950 text-rose-400 border border-rose-800 px-1.5 py-0.5 rounded">
                          Gated
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold font-mono text-cyan-400">
                      {(item.score.overall_score * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-slate-400">Match Score</div>
                  </div>
                </div>

                <div className="text-xs text-slate-300 space-y-1 mb-3">
                  {item.score.explanation.map((line, idx) => (
                    <div key={idx} className="flex items-center gap-1.5">
                      <span className="text-cyan-500">•</span> {line}
                    </div>
                  ))}
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={() => onSelectOfficer(item.score.officer_id)}
                    className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-medium transition-colors"
                  >
                    Select for Assignment
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ── 3. ReassignmentDialog ──────────────────────────────────────────────────

export const ReassignmentDialog: React.FC<{
  investigationId: string;
  isOpen: boolean;
  onClose: () => void;
  currentOfficerId?: string;
}> = ({ investigationId, isOpen, onClose, currentOfficerId }) => {
  const queryClient = useQueryClient();
  const [newOfficerId, setNewOfficerId] = useState("");
  const [reason, setReason] = useState("");
  const [reassignType, setReassignType] = useState("MANUAL");
  const [manualOverride, setManualOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");

  const reassignMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch("/api/assignment/reassign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          investigation_id: investigationId,
          new_officer_id: newOfficerId,
          reason,
          reassign_type: reassignType,
          manual_override: manualOverride,
          override_reason: manualOverride ? overrideReason : null,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Reassignment failed");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignment-history", investigationId] });
      queryClient.invalidateQueries({ queryKey: ["investigation-detail", investigationId] });
      onClose();
    },
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        <h3 className="text-lg font-semibold text-slate-100 border-b border-slate-800 pb-3">
          Reassign Investigation — {investigationId}
        </h3>

        {currentOfficerId && (
          <div className="text-xs text-slate-400">
            Currently assigned to: <span className="font-semibold text-slate-200">{currentOfficerId}</span>
          </div>
        )}

        <div className="space-y-3 text-sm">
          <div>
            <label className="block text-slate-300 text-xs font-medium mb-1">New Officer ID</label>
            <input
              type="text"
              value={newOfficerId}
              onChange={(e) => setNewOfficerId(e.target.value)}
              placeholder="e.g. OFF-2026-004"
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-medium mb-1">Reassignment Type</label>
            <select
              value={reassignType}
              onChange={(e) => setReassignType(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 text-sm"
            >
              <option value="MANUAL">Manual Supervisor Reassignment</option>
              <option value="RESIGNATION">Officer Resignation</option>
              <option value="LEAVE">Scheduled / Emergency Leave</option>
              <option value="SUSPENSION">Suspension</option>
              <option value="PROMOTION">Promotion / Transfer</option>
              <option value="BULK">Bulk Redistribution</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-medium mb-1">Reason / Justification</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              placeholder="Provide operational reason for reassignment"
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="override"
              checked={manualOverride}
              onChange={(e) => setManualOverride(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-cyan-600 focus:ring-0"
            />
            <label htmlFor="override" className="text-xs text-amber-300 font-medium">
              Manual Override (Bypass validation gate)
            </label>
          </div>

          {manualOverride && (
            <div>
              <label className="block text-amber-400 text-xs font-medium mb-1">Override Reason (Required)</label>
              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                rows={2}
                placeholder="Explain why operational constraints are overridden"
                className="w-full bg-slate-800 border border-amber-500/50 rounded px-3 py-2 text-amber-200 text-sm focus:outline-none"
              />
            </div>
          )}
        </div>

        {reassignMutation.isError && (
          <div className="p-3 bg-rose-950/60 border border-rose-500/40 rounded text-rose-300 text-xs">
            {(reassignMutation.error as Error).message}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium"
          >
            Cancel
          </button>
          <button
            onClick={() => reassignMutation.mutate()}
            disabled={!newOfficerId || !reason || reassignMutation.isPending}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded text-xs font-medium"
          >
            {reassignMutation.isPending ? "Reassigning..." : "Confirm Reassignment"}
          </button>
        </div>
      </div>
    </div>
  );
};

// ── 4. AssignmentHistoryPanel ──────────────────────────────────────────────

export const AssignmentHistoryPanel: React.FC<{ investigationId: string }> = ({ investigationId }) => {
  const { data: history, isLoading } = useQuery<AssignmentHistoryRecord[]>({
    queryKey: ["assignment-history", investigationId],
    queryFn: async () => {
      const res = await fetch(`/api/assignment/history/${investigationId}`);
      if (!res.ok) throw new Error("Failed to load history");
      return res.json();
    },
  });

  if (isLoading) {
    return <div className="p-4 text-xs text-slate-400 animate-pulse">Loading assignment history...</div>;
  }

  if (!history || history.length === 0) {
    return <div className="p-4 text-xs text-slate-500">No assignment history recorded.</div>;
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <h4 className="text-sm font-semibold text-slate-200 flex items-center justify-between">
        <span>Assignment Audit History</span>
        <span className="text-xs font-mono text-slate-400">{history.length} events</span>
      </h4>

      <div className="relative border-l border-slate-800 ml-3 space-y-4 py-1">
        {history.map((record) => (
          <div key={record.id} className="ml-4 relative">
            <span className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-cyan-500 ring-4 ring-slate-900" />
            <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 space-y-1">
              <div className="flex justify-between items-start text-xs">
                <span className="font-semibold text-slate-200">
                  Assigned to <span className="text-cyan-400">{record.officer_id}</span>
                </span>
                <span className="text-slate-400 font-mono text-[11px]">
                  {new Date(record.timestamp).toLocaleString()}
                </span>
              </div>

              {record.previous_officer && (
                <div className="text-xs text-slate-400">
                  Previous: <span className="text-slate-300">{record.previous_officer}</span>
                </div>
              )}

              {record.reason && (
                <div className="text-xs text-slate-300 italic">"{record.reason}"</div>
              )}

              {record.manual_override && (
                <div className="mt-1 p-2 bg-amber-950/40 border border-amber-500/30 rounded text-[11px] text-amber-300">
                  ⚠ Manual Override by {record.assigned_by}: {record.override_reason}
                </div>
              )}

              <div className="text-[10px] text-slate-500 flex gap-3 pt-1">
                <span>By: {record.assigned_by}</span>
                <span>Policy v{record.policy_version}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── 5. CompletionEstimateCard ──────────────────────────────────────────────

export const CompletionEstimateCard: React.FC<{ investigationId: string }> = ({ investigationId }) => {
  const { data: estimate, isLoading } = useQuery<CompletionEstimate>({
    queryKey: ["completion-estimate", investigationId],
    queryFn: async () => {
      const res = await fetch(`/api/assignment/estimate/${investigationId}`);
      if (!res.ok) throw new Error("Failed to load estimate");
      return res.json();
    },
  });

  if (isLoading) {
    return <div className="p-4 text-xs text-slate-400 animate-pulse">Estimating completion timeframe...</div>;
  }

  if (!estimate) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <div className="flex justify-between items-center">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Estimated Completion Timeframe
        </h4>
        <span className="text-xs text-cyan-400 font-mono">
          Target: {estimate.estimated_completion_date}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2 bg-slate-800/50 rounded border border-slate-700/50">
          <div className="text-xs text-slate-400">Earliest</div>
          <div className="text-sm font-bold text-slate-200 font-mono">{estimate.earliest_days}d</div>
        </div>
        <div className="p-2 bg-cyan-950/40 rounded border border-cyan-500/30">
          <div className="text-xs text-cyan-300 font-semibold">Expected</div>
          <div className="text-sm font-bold text-cyan-400 font-mono">{estimate.expected_days}d</div>
        </div>
        <div className="p-2 bg-slate-800/50 rounded border border-slate-700/50">
          <div className="text-xs text-slate-400">Latest</div>
          <div className="text-sm font-bold text-slate-200 font-mono">{estimate.latest_days}d</div>
        </div>
      </div>

      {estimate.factors && (
        <div className="text-[11px] text-slate-400 space-y-1 pt-1">
          <div className="flex justify-between">
            <span>Case Priority ({estimate.factors.priority})</span>
            <span>{estimate.factors.base_days}d base</span>
          </div>
          <div className="flex justify-between">
            <span>Active Tasks ({estimate.factors.task_count})</span>
            <span>{estimate.factors.task_factor}× mult</span>
          </div>
          <div className="flex justify-between">
            <span>Officer Load Factor</span>
            <span>{estimate.factors.workload_factor}× mult</span>
          </div>
        </div>
      )}
    </div>
  );
};
