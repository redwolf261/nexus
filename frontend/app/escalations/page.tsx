"use client";

import { useEscalationQueue } from "@/hooks/useApi";
import { EscalationQueue } from "@/components/escalation/EscalationQueue";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function EscalationsPage() {
  const { data, isLoading, error, refetch } = useEscalationQueue();
  
  const escalations = Array.isArray(data) ? data : (data as any)?.items ?? [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <div>
            <h1 className="text-2xl font-bold font-mono text-slate-100">Escalation Queue</h1>
            <p className="text-slate-400 text-sm">SLA breaches · Unresolved flags · Escalation history</p>
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
          Loading escalation queue...
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/50 rounded-lg text-rose-300 text-sm font-mono">
          ⚠ Failed to load escalations. Backend may be starting up.
        </div>
      )}

      {!isLoading && (
        <EscalationQueue
          escalations={escalations}
          onRefresh={() => refetch()}
        />
      )}
    </div>
  );
}
