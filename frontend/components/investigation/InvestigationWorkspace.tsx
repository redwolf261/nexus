import React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { OperationalStatusCard } from "./OperationalStatusCard";
import { HealthCard } from "./HealthCard";
import { DecisionSupportPanel } from "./DecisionSupportPanel";
import { TimelinePanel } from "./TimelinePanel";
import { SupervisorActions } from "./SupervisorActions";
import { EvidenceSummary } from "./EvidenceSummary";
import { RecentActivity } from "./RecentActivity";

interface InvestigationWorkspaceProps {
  investigationId: string;
}

export const InvestigationWorkspace: React.FC<InvestigationWorkspaceProps> = ({ investigationId }) => {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["investigation-workspace", investigationId],
    queryFn: async () => {
      const res = await fetch(`/api/workspace/${investigationId}`);
      if (!res.ok) throw new Error("Failed to load investigation workspace payload");
      return res.json();
    },
    refetchInterval: 15000,
  });

  const handleExecuteAction = async (actionType: string, payload: any) => {
    const res = await fetch(`/api/workspace/${investigationId}/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Action execution failed");
    }
    await refetch();
    queryClient.invalidateQueries({ queryKey: ["supervisor-command-center"] });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 p-6 text-slate-100 flex items-center justify-center">
        <div className="text-sm text-indigo-400 font-mono animate-pulse">
          Loading Supervisor Investigation Operational Workspace ({investigationId})...
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen bg-slate-950 p-6 text-slate-100 flex items-center justify-center">
        <div className="p-4 bg-rose-950/80 border border-rose-500 rounded-xl text-rose-300 text-sm">
          Failed to load investigation workspace for '{investigationId}'.
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Top Header & Operational Status Card */}
      <OperationalStatusCard
        summary={data.summary}
        ageHours={data.case_age_hours}
        slaPct={data.sla_utilization_pct}
      />

      {/* Main Operational Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2/3): Timeline & Evidence */}
        <div className="lg:col-span-2 space-y-6">
          <TimelinePanel events={data.timeline_summary} />
          <EvidenceSummary evidence={data.evidence_summary} />
        </div>

        {/* Right Column (1/3): Health, Decision Support & Actions */}
        <div className="space-y-6">
          <HealthCard health={data.health} />
          <DecisionSupportPanel recommendations={data.recommendations} />
          <SupervisorActions investigationId={investigationId} onActionExecute={handleExecuteAction} />
          <RecentActivity activity={data.recent_activity} />
        </div>
      </div>
    </div>
  );
};

export default InvestigationWorkspace;
