import React from "react";
import { useQuery } from "@tanstack/react-query";

import { ExecutiveSummary } from "./ExecutiveSummary";
import { KPIWidgets } from "./KPIWidgets";
import { DistrictOverview } from "./DistrictOverview";
import { TrendCharts } from "./TrendCharts";
import { HeatmapPanel } from "./HeatmapPanel";

export const ExecutiveDashboard: React.FC = () => {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["executive-dashboard"],
    queryFn: async () => {
      const res = await fetch("/api/executive/dashboard");
      if (!res.ok) throw new Error("Failed to load executive dashboard payload");
      return res.json();
    },
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 p-6 text-slate-100 flex items-center justify-center">
        <div className="text-sm text-indigo-400 font-mono animate-pulse">
          Loading Executive Command Oversight Dashboard...
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen bg-slate-950 p-6 text-slate-100 flex items-center justify-center">
        <div className="p-4 bg-rose-950/80 border border-rose-500 rounded-xl text-rose-300 text-sm">
          Failed to load executive dashboard payload.
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Top Executive Summary Header */}
      <ExecutiveSummary summary={data.summary_metrics} scopeRole={data.scope_role} />

      {/* KPI Metric Cards */}
      <KPIWidgets kpis={data.kpis} />

      {/* Main Grid: Districts & Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DistrictOverview districts={data.district_analytics} />
        <TrendCharts trends={data.trends} />
      </div>

      {/* District Heatmaps Panel */}
      <HeatmapPanel heatmaps={data.heatmaps} />
    </div>
  );
};

export default ExecutiveDashboard;
