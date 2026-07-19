"use client";

import { useExecutiveDashboard } from "@/hooks/useApi";
import { MetricCard } from "@/components/shared/MetricCard";
import { Activity, MapPin, Network, ShieldAlert, Timer, TrendingUp } from "lucide-react";
import { ThreatPanel } from "@/components/dashboard/ThreatPanel";
import { useDemo } from "@/contexts/DemoContext";

export default function ExecutiveDashboard() {
  const { data: dashboard, isLoading, error } = useExecutiveDashboard();
  const { stage } = useDemo();

  if (isLoading) {
    return <div className="p-8 text-muted-foreground animate-pulse font-mono tracking-widest">INITIALIZING SECURE UPLINK...</div>;
  }

  if (error || !dashboard) {
    return <div className="p-8 text-destructive font-mono">ERROR: UPLINK FAILED.</div>;
  }

  // Determine threat level dynamically
  let threatLevel: "LOW" | "GUARDED" | "ELEVATED" | "HIGH" | "CRITICAL" = "ELEVATED";
  if (stage === "LIVE_INCIDENT" || stage === "THREAT_UPDATE") {
    threatLevel = "CRITICAL";
  }

  return (
    <div className="p-8 flex flex-col gap-8 h-full">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Executive Command</h1>
          <p className="text-muted-foreground mt-1">Real-time intelligence and tactical operations overview.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
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
          title="Avg Invest. Time" 
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
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 flex-1">
        <div className="xl:col-span-2 bg-card border border-border rounded-lg p-6 flex flex-col items-center justify-center relative overflow-hidden">
          {/* Tactical wireframe background pattern */}
          <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]" />
          
          <div className="text-center relative z-10">
            <TrendingUp className="w-12 h-12 text-primary mx-auto mb-4 opacity-50" />
            <span className="text-primary font-mono tracking-widest uppercase">
              {stage === "THREAT_UPDATE" ? "CRITICAL THREAT INJECTED — ALL SYSTEMS RE-ROUTING" : "SYSTEMS NOMINAL — WAITING FOR TACTICAL INPUT"}
            </span>
          </div>
        </div>
        
        <div className="h-full">
          <ThreatPanel level={threatLevel} />
        </div>
      </div>
    </div>
  );
}
