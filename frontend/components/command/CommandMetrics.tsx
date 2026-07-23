import React from "react";

export interface CommandMetricsProps {
  metrics?: {
    open_investigations: number;
    avg_workload_weight: number;
    avg_assignment_delay_hours: number;
    approvals_pending: number;
    critical_alerts_count: number;
    analysts_online: number;
    cases_nearing_sla: number;
  };
}

export const CommandMetrics: React.FC<CommandMetricsProps> = ({ metrics }) => {
  if (!metrics) return null;

  const cards = [
    { label: "Active Investigations", value: metrics.open_investigations, color: "border-cyan-500/40 text-cyan-400" },
    { label: "Avg Workload Weight", value: metrics.avg_workload_weight, color: "border-indigo-500/40 text-indigo-400" },
    { label: "Avg Assignment Delay", value: `${metrics.avg_assignment_delay_hours}h`, color: "border-amber-500/40 text-amber-400" },
    { label: "Pending Approvals", value: metrics.approvals_pending, color: "border-purple-500/40 text-purple-400" },
    { label: "Critical Alerts", value: metrics.critical_alerts_count, color: "border-rose-500/40 text-rose-400" },
    { label: "Analysts Online", value: metrics.analysts_online, color: "border-emerald-500/40 text-emerald-400" },
    { label: "Cases Nearing SLA", value: metrics.cases_nearing_sla, color: "border-red-500/40 text-red-400" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
      {cards.map((c, i) => (
        <div key={i} className={`p-3 bg-slate-900/90 border ${c.color} rounded-xl shadow-lg flex flex-col justify-between`}>
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">{c.label}</div>
          <div className={`text-xl font-bold font-mono mt-1 ${c.color.split(" ")[1]}`}>{c.value}</div>
        </div>
      ))}
    </div>
  );
};
