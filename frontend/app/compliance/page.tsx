"use client";

import { useComplianceDashboard } from "@/hooks/useApi";
import { ComplianceDashboard } from "@/components/compliance/ComplianceDashboard";
import { ApiClient } from "@/services/apiClient";
import { ClipboardList, RefreshCw } from "lucide-react";
import { useCallback } from "react";

export default function CompliancePage() {
  const { data, isLoading, error, refetch } = useComplianceDashboard();

  const dashboardData = data ?? {};
  const rules = (data as any)?.rules ?? [];

  const handleTriggerScan = useCallback(async () => {
    const result = await ApiClient.getComplianceDashboard();
    refetch();
    return result;
  }, [refetch]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ClipboardList className="w-5 h-5 text-cyan-400" />
          <div>
            <h1 className="text-2xl font-bold font-mono text-slate-100">Compliance Monitoring</h1>
            <p className="text-slate-400 text-sm">20-rule engine · SLA compliance · Active violations · Rule registry</p>
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
          Loading compliance engine...
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/50 rounded-lg text-rose-300 text-sm font-mono">
          ⚠ Failed to load compliance data.
        </div>
      )}

      {!isLoading && (
        <ComplianceDashboard
          dashboardData={dashboardData}
          rules={rules}
          onTriggerScan={handleTriggerScan}
        />
      )}
    </div>
  );
}
