import React from "react";

interface ExecutiveSummaryProps {
  summary: Record<string, any>;
  scopeRole: string;
}

export const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({ summary, scopeRole }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <h2 className="text-base font-bold text-slate-100">Executive Command Center Summary</h2>
        <span className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-700 rounded font-mono font-bold text-xs">
          Role Scope: {scopeRole}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-800/50 p-3 rounded-lg border border-slate-700 text-xs">
        <div>
          <span className="text-slate-400 block text-[11px]">Total Active Cases</span>
          <span className="text-lg font-bold text-slate-100 font-mono">{summary.total_active_cases || 0}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Total Closed Cases</span>
          <span className="text-lg font-bold text-slate-200 font-mono">{summary.total_closed_cases || 0}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Statewide SLA Avg</span>
          <span className="text-lg font-bold text-emerald-400 font-mono">{summary.avg_statewide_sla_pct || 0}%</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Critical Cases</span>
          <span className="text-lg font-bold text-rose-400 font-mono">{summary.critical_cases_total || 0}</span>
        </div>
      </div>
    </div>
  );
};

export default ExecutiveSummary;
