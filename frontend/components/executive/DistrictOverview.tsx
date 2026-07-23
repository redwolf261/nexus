import React from "react";

export interface DistrictAnalytics {
  district_id: string;
  district_name: string;
  rank: number;
  active_cases: number;
  closed_cases: number;
  backlog_count: number;
  sla_compliance_pct: number;
  avg_approval_delay_hours: number;
  officer_utilization_pct: number;
  supervisor_utilization_pct: number;
  burnout_risk_score: number;
  critical_cases_count: number;
  district_health_score: number;
}

interface DistrictOverviewProps {
  districts: DistrictAnalytics[];
}

export const DistrictOverview: React.FC<DistrictOverviewProps> = ({ districts }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <h3 className="font-semibold text-slate-200">District Operational Performance & Rankings</h3>
        <span className="text-[11px] text-cyan-400 font-mono">Multi-District Scoped</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
              <th className="py-2 px-2">Rank</th>
              <th className="py-2 px-2">District</th>
              <th className="py-2 px-2 text-right">Active</th>
              <th className="py-2 px-2 text-right">Closed</th>
              <th className="py-2 px-2 text-right">SLA %</th>
              <th className="py-2 px-2 text-right">Burnout Risk</th>
              <th className="py-2 px-2 text-right">Health Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {districts?.map((d) => (
              <tr key={d.district_id} className="hover:bg-slate-800/40">
                <td className="py-2 px-2 font-bold font-mono text-cyan-400">#{d.rank}</td>
                <td className="py-2 px-2 font-medium text-slate-200">{d.district_name}</td>
                <td className="py-2 px-2 text-right text-slate-100 font-mono">{d.active_cases}</td>
                <td className="py-2 px-2 text-right text-slate-300 font-mono">{d.closed_cases}</td>
                <td className={`py-2 px-2 text-right font-mono font-bold ${d.sla_compliance_pct >= 90 ? "text-emerald-400" : "text-amber-400"}`}>
                  {d.sla_compliance_pct}%
                </td>
                <td className="py-2 px-2 text-right text-rose-300 font-mono">{d.burnout_risk_score}</td>
                <td className="py-2 px-2 text-right font-bold text-slate-100 font-mono">{d.district_health_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DistrictOverview;
