import React, { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { CommandMetrics } from "./CommandMetrics";
import { WorkloadPanel } from "./WorkloadPanel";
import { ApprovalQueue } from "./ApprovalQueue";
import { SLAAlerts } from "./SLAAlerts";
import { IntelligenceFeed } from "./IntelligenceFeed";
import { PresenceBanner, PresenceUser } from "./PresenceBanner";
import { NotificationToast, NotificationDigest } from "./NotificationToast";

export const SupervisorDashboard: React.FC = () => {
  const [sortBy, setSortBy] = useState<string>("sla_risk");
  const [presenceList, setPresenceList] = useState<PresenceUser[]>([]);
  const [notifications, setNotifications] = useState<NotificationDigest[]>([]);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["supervisor-command-center", sortBy],
    queryFn: async () => {
      const res = await fetch(`/api/command-center/dashboard?sort_cases_by=${sortBy}`);
      if (!res.ok) throw new Error("Failed to load command center payload");
      return res.json();
    },
    refetchInterval: 15000, // Fallback background sync
  });

  // Fetch live presence
  useEffect(() => {
    const fetchPresence = async () => {
      try {
        const res = await fetch("/api/command-center/presence");
        if (res.ok) {
          const list = await res.json();
          setPresenceList(list);
        }
      } catch (err) {
        // Silent presence fallback
      }
    };
    fetchPresence();
    const interval = setInterval(fetchPresence, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleDismissNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.digest_id !== id));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 p-6 text-slate-100 flex items-center justify-center">
        <div className="text-sm text-cyan-400 font-mono animate-pulse">Initializing Supervisor Command Console...</div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen bg-slate-950 p-6 text-slate-100 flex items-center justify-center">
        <div className="p-4 bg-rose-950/80 border border-rose-500 rounded-xl text-rose-300 text-sm">
          Failed to load Supervisor Command Center workspace.
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header Bar */}
      <header className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">NEXUS Supervisor Command Console</h1>
          <p className="text-xs text-slate-400">Real-Time Operational Command, Live Collaboration & SLA Health Workstation</p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-slate-400 font-mono">Last Sync: {new Date(data.generated_at).toLocaleTimeString()}</span>
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 rounded font-medium"
          >
            Refresh Feed
          </button>
        </div>
      </header>

      {/* Live Collaboration Presence Banner */}
      <PresenceBanner presenceList={presenceList} />

      {/* Operational Metrics Bar */}
      <CommandMetrics metrics={data.metrics} />

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Active Investigations */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h2 className="text-sm font-semibold text-slate-200">Active Investigations Workspace</h2>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Sort By:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs"
              >
                <option value="sla_risk">SLA Risk</option>
                <option value="priority">Priority</option>
                <option value="workload">Workload Weight</option>
                <option value="assignment_date">Assignment Date</option>
              </select>
            </div>
          </div>

          <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
            {data.active_cases?.map((c: any) => (
              <div key={c.id} className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-lg space-y-2 text-xs">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="font-bold text-slate-100">{c.title}</span>
                    <span className="font-mono text-cyan-400 ml-2">({c.id})</span>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Investigator: <span className="font-mono text-slate-300">{c.assigned_officer_name}</span> | Priority: <span className="font-semibold text-amber-400">{c.priority}</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 bg-slate-900 border border-slate-700 rounded font-mono text-[10px] text-slate-300">
                    Status: {c.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 bg-slate-900/50 p-2 rounded text-[11px]">
                  <div><span className="text-slate-400">Progress:</span> <span className="font-semibold text-emerald-400">{c.progress_pct}%</span></div>
                  <div><span className="text-slate-400">Workload Weight:</span> <span className="font-semibold text-indigo-400">{c.workload_weight}</span></div>
                  <div><span className="text-slate-400">Age:</span> <span className="font-semibold text-slate-200">{c.assignment_age_hours.toFixed(1)}h</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Workload Panel & Approval Queue */}
        <div className="space-y-6">
          <WorkloadPanel analysts={data.analyst_workloads} />
          <ApprovalQueue approvals={data.approval_queue} />
        </div>
      </div>

      {/* Bottom Row: SLA Alerts & Intelligence Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SLAAlerts alerts={data.sla_alerts} />
        <IntelligenceFeed feed={data.intelligence_feed} />
      </div>

      {/* Notification Toast Component */}
      <NotificationToast notifications={notifications} onDismiss={handleDismissNotification} />
    </div>
  );
};

export default SupervisorDashboard;
