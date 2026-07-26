"use client";

import { useApprovalQueue } from "@/hooks/useApi";
import { ApprovalQueue } from "@/components/approval/ApprovalQueue";
import { CheckCircle, RefreshCw } from "lucide-react";

export default function ApprovalsPage() {
  const { data, isLoading, error, refetch } = useApprovalQueue();
  
  const approvals = Array.isArray(data) ? data : (data as any)?.items ?? [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <div>
            <h1 className="text-2xl font-bold font-mono text-slate-100">Approval Workflow</h1>
            <p className="text-slate-400 text-sm">Supervisor decision queue · Pending authorizations · Decision history</p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 p-8 text-slate-400 font-mono text-sm animate-pulse">
          <RefreshCw className="w-4 h-4 animate-spin" />
          Loading approval queue...
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/50 rounded-lg text-rose-300 text-sm font-mono">
          ⚠ Failed to load approvals. Backend may be starting up.
        </div>
      )}

      {!isLoading && (
        <ApprovalQueue
          approvals={approvals}
          onRefresh={() => refetch()}
        />
      )}
    </div>
  );
}
