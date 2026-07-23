import React from "react";

export interface KPIData {
  kpi_id: string;
  name: string;
  category: string;
  value: number;
  unit: string;
  formula: string;
  explanation: string;
  trend: "UP" | "DOWN" | "STABLE" | string;
  confidence_score: number;
  timestamp: string;
}

interface KPIWidgetsProps {
  kpis: KPIData[];
}

export const KPIWidgets: React.FC<KPIWidgetsProps> = ({ kpis }) => {
  const getTrendIcon = (trend: string) => {
    switch (trend.toUpperCase()) {
      case "UP":
        return <span className="text-emerald-400 font-bold">▲</span>;
      case "DOWN":
        return <span className="text-rose-400 font-bold">▼</span>;
      default:
        return <span className="text-sky-400 font-bold">▶</span>;
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-200">Executive Key Performance Indicators</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
        {kpis?.map((kpi) => (
          <div key={kpi.kpi_id} className="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-2">
            <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono">
              <span>{kpi.category}</span>
              {getTrendIcon(kpi.trend)}
            </div>
            <div className="space-y-0.5">
              <span className="text-[11px] text-slate-300 block font-medium truncate">{kpi.name}</span>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold text-slate-100">{kpi.value}</span>
                <span className="text-[10px] text-slate-400 font-mono">{kpi.unit}</span>
              </div>
            </div>
            <div className="pt-2 border-t border-slate-800/80 text-[9px] text-slate-400 space-y-0.5">
              <p className="truncate font-mono">Formula: {kpi.formula}</p>
              <p className="truncate text-slate-300">{kpi.explanation}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KPIWidgets;
