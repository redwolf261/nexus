import React from "react";

export interface SLAAlert {
  task_id: string;
  investigation_id: string;
  task_title: string;
  assigned_officer_id?: string;
  sla_category: string;
  remaining_sla_seconds: number;
  due_at?: string;
  breach_age_hours?: number;
  recommended_action: string;
}

export const SLAAlerts: React.FC<{ alerts?: SLAAlert[] }> = ({ alerts }) => {
  if (!alerts || alerts.length === 0) {
    return <div className="text-xs text-slate-500 py-4 text-center">All tasks operating within normal SLA bounds.</div>;
  }

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case "CRITICAL":
        return "bg-rose-950 text-rose-300 border-rose-800";
      case "RED":
        return "bg-red-950 text-red-300 border-red-800";
      case "YELLOW":
        return "bg-amber-950 text-amber-300 border-amber-800";
      default:
        return "bg-emerald-950 text-emerald-300 border-emerald-800";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-semibold text-slate-200 flex justify-between items-center">
        <span>SLA Health & Risk Monitor</span>
        <span className="text-xs font-mono text-cyan-400">{alerts.length} Active SLA Tasks</span>
      </h3>

      <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
        {alerts.map((item) => (
          <div key={item.task_id} className="p-3 bg-slate-800/80 border border-slate-700 rounded-lg space-y-2 text-xs">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-semibold text-slate-200">{item.task_title}</div>
                <div className="font-mono text-slate-400 text-[11px]">Case: {item.investigation_id} | Officer: {item.assigned_officer_id || "Unassigned"}</div>
              </div>
              <span className={`px-2 py-0.5 rounded border font-bold text-[10px] ${getCategoryBadge(item.sla_category)}`}>
                {item.sla_category}
              </span>
            </div>

            <div className="p-2 bg-slate-900/60 rounded border border-slate-800 text-[11px] text-slate-300">
              <span className="font-semibold text-cyan-400">Action:</span> {item.recommended_action}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
