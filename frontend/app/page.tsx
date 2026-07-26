"use client";

import { useExecutiveDashboard } from "@/hooks/useApi";
import { MetricCard } from "@/components/shared/MetricCard";
import { MetricCardSkeleton } from "@/components/shared/Skeleton";
import { Activity, MapPin, Network, ShieldAlert, Timer, TrendingUp, AlertOctagon } from "lucide-react";
import { ThreatPanel } from "@/components/dashboard/ThreatPanel";
import { useDemo } from "@/contexts/DemoContext";

export default function ExecutiveDashboard() {
  const { data: dashboard, isLoading, error } = useExecutiveDashboard();
  const { stage } = useDemo();

  let threatLevel: "LOW" | "GUARDED" | "ELEVATED" | "HIGH" | "CRITICAL" = "ELEVATED";
  if (stage === "LIVE_INCIDENT" || stage === "THREAT_UPDATE") {
    threatLevel = "CRITICAL";
  }

  return (
    <div className="p-6 flex flex-col gap-6 h-full relative">
      {/* Dot-grid background */}
      <div className="absolute inset-0 dot-grid opacity-[0.35] pointer-events-none" />

      {/* Header */}
      <div className="relative flex items-end justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            <span className="text-[9px] font-mono text-primary uppercase tracking-[0.25em]">
              Executive Command Layer
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Intelligence Overview
          </h1>
          <p className="text-muted-foreground text-sm mt-0.5">
            Real-time operational metrics · Karnataka State Police
          </p>
        </div>

        {stage === "LIVE_INCIDENT" && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-destructive/15 border border-destructive/40 animate-pulse">
            <AlertOctagon className="w-4 h-4 text-destructive" />
            <span className="text-destructive font-mono font-bold text-xs tracking-widest">
              CRITICAL INCIDENT ACTIVE
            </span>
          </div>
        )}
      </div>

      {/* Metric cards */}
      <div className="relative grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => <MetricCardSkeleton key={i} />)
        ) : error ? (
          <div className="col-span-6 p-4 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs font-mono">
            ⚠ Failed to load dashboard metrics. Check backend connection.
          </div>
        ) : dashboard ? (
          <>
            <MetricCard
              title="Today's FIRs"
              value={dashboard.todays_firs}
              icon={Activity}
              trend="+12%"
              trendUp={false}
            />
            <MetricCard
              title="Active Campaigns"
              value={dashboard.active_campaigns}
              icon={Network}
            />
            <MetricCard
              title="Predicted Hotspots"
              value={dashboard.predicted_hotspots}
              icon={MapPin}
              trend="-4%"
              trendUp={true}
            />
            <MetricCard
              title="Avg. Invest. Time"
              value={`${dashboard.average_investigation_time}d`}
              icon={Timer}
            />
            <MetricCard
              title="Intel Alerts"
              value={dashboard.new_intelligence_alerts}
              icon={ShieldAlert}
              trend="Critical"
              trendUp={false}
            />
            <MetricCard
              title="Crime Trend"
              value="High"
              icon={TrendingUp}
            />
          </>
        ) : null}
      </div>

      {/* Main content area */}
      <div className="relative grid grid-cols-1 xl:grid-cols-3 gap-5 flex-1 min-h-0">
        {/* Map / status panel */}
        <div className="xl:col-span-2 glass-card rounded-xl p-6 flex flex-col items-center justify-center relative overflow-hidden min-h-[280px]">
          {/* Scanlines overlay */}
          <div className="absolute inset-0 scanlines rounded-xl" />
          {/* Radial glow */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,oklch(0.72_0.17_162/0.04)_0%,transparent_70%)]" />

          <div className="relative z-10 text-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto">
              <TrendingUp className="w-6 h-6 text-primary" />
            </div>
            <div className="space-y-1">
              <div className="text-primary font-mono font-bold tracking-widest uppercase text-xs">
                {stage === "THREAT_UPDATE"
                  ? "⚠ CRITICAL THREAT INJECTED — RE-ROUTING ALL SYSTEMS"
                  : "SYSTEMS NOMINAL — AWAITING TACTICAL INPUT"}
              </div>
              <div className="text-muted-foreground text-[10px] font-mono">
                Navigate to Predictive Map for GIS intelligence layer
              </div>
            </div>
          </div>
        </div>

        {/* Threat panel */}
        <div className="min-h-[280px]">
          <ThreatPanel level={threatLevel} />
        </div>
      </div>
    </div>
  );
}
