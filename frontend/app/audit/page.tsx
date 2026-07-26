"use client";

import { useAuditLedger } from "@/hooks/useApi";
import { AuditTimeline } from "@/components/audit/AuditTimeline";
import { AuditSearchPanel } from "@/components/audit/AuditSearchPanel";
import { IntegrityStatusWidget } from "@/components/audit/IntegrityStatusWidget";
import { ApiClient } from "@/services/apiClient";
import { Shield, RefreshCw } from "lucide-react";
import { useState, useCallback } from "react";

export default function AuditPage() {
  const { data, isLoading, error, refetch } = useAuditLedger();
  const [filters, setFilters] = useState({});

  const entries = Array.isArray(data) ? data : (data as any)?.entries ?? [];

  const handleSearch = useCallback((f: any) => {
    setFilters(f);
    refetch();
  }, [refetch]);

  const handleVerifyIntegrity = useCallback(async () => {
    return ApiClient.verifyAuditIntegrity();
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-5 h-5 text-purple-400" />
          <div>
            <h1 className="text-2xl font-bold font-mono text-slate-100">Audit Ledger</h1>
            <p className="text-slate-400 text-sm">SHA-256 immutable chain · Event log · Integrity verification</p>
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
          Loading audit ledger...
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/50 rounded-lg text-rose-300 text-sm font-mono">
          ⚠ Failed to load audit ledger.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <div className="xl:col-span-3 space-y-6">
          <AuditSearchPanel onSearch={handleSearch} />
          {!isLoading && <AuditTimeline entries={entries} />}
        </div>
        <div>
          <IntegrityStatusWidget onVerifyRequest={handleVerifyIntegrity} />
        </div>
      </div>
    </div>
  );
}
