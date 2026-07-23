import React from "react";

export interface AnalystWorkload {
  officer_id: string;
  name: string;
  rank: string;
  district_id?: str;
  availability_status: string;
  current_case_count: number;
  current_task_count: number;
  weighted_workload: number;
  burnout_score: number;
  burnout_risk_band: string;
  capacity_used_pct: number;
  skills: string[];
}

export const WorkloadPanel: React.FC<{ analysts?: AnalystWorkload[] }> = ({ analysts }) => {
  if (!analysts || analysts.length === 0) {
    return <div className="text-xs text-slate-500 py-4 text-center">No analyst workload data available.</div>;
  }

  const getBurnoutBadge = (score: number, band: string) => {
    if (score >= 75) return "bg-rose-950 text-rose-300 border-rose-800";
    if (score >= 50) return "bg-amber-950 text-amber-300 border-amber-800";
    return "bg-emerald-950 text-emerald-300 border-emerald-800";
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-semibold text-slate-200 flex justify-between items-center">
        <span>Analyst Workload & Burnout Monitor</span>
        <span className="text-xs font-mono text-cyan-400">{analysts.length} Investigators</span>
      </h3>

      <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
        {analysts.map((a) => (
          <div key={a.officer_id} className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-lg space-y-2 text-xs">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-bold text-slate-100">{a.name}</span>
                <span className="text-slate-400 font-mono ml-2">({a.officer_id})</span>
                <div className="text-[11px] text-slate-400">{a.rank} — District: {a.district_id || "N/A"}</div>
              </div>
              <span className={`px-2 py-0.5 rounded border text-[10px] font-bold font-mono ${getBurnoutBadge(a.burnout_score, a.burnout_risk_band)}`}>
                Burnout {a.burnout_score.toFixed(0)}/100 ({a.burnout_risk_band})
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 py-1 bg-slate-900/50 rounded px-2 text-[11px]">
              <div><span className="text-slate-400">Cases:</span> <span className="font-semibold text-slate-200">{a.current_case_count}</span></div>
              <div><span className="text-slate-400">Tasks:</span> <span className="font-semibold text-slate-200">{a.current_task_count}</span></div>
              <div><span className="text-slate-400">Capacity:</span> <span className={`font-semibold ${a.capacity_used_pct >= 100 ? "text-rose-400" : "text-emerald-400"}`}>{a.capacity_used_pct.toFixed(0)}%</span></div>
            </div>

            {a.skills && a.skills.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {a.skills.map((s, idx) => (
                  <span key={idx} className="px-1.5 py-0.5 bg-slate-900 text-slate-300 text-[10px] rounded border border-slate-700 font-mono">
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
