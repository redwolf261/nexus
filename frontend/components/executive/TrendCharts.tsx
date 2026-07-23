import React from "react";

export interface TrendData {
  metric_name: string;
  period: string;
  current_value: number;
  previous_value: number;
  change_pct: number;
  moving_average: number;
  direction: "UP" | "DOWN" | "STABLE" | string;
}

interface TrendChartsProps {
  trends: TrendData[];
}

export const TrendCharts: React.FC<TrendChartsProps> = ({ trends }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="border-b border-slate-800 pb-2">
        <h3 className="font-semibold text-slate-200">Deterministic Multi-Period Trend Statistics</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {trends?.map((t, idx) => (
          <div key={idx} className="p-3 bg-slate-800/60 rounded border border-slate-700 space-y-1">
            <div className="flex justify-between font-medium text-slate-200">
              <span>{t.metric_name}</span>
              <span className="text-[10px] text-cyan-400 font-mono">[{t.period}]</span>
            </div>
            <div className="flex justify-between items-baseline pt-1">
              <span className="text-lg font-bold text-slate-100">{t.current_value}</span>
              <span className={`text-xs font-mono font-bold ${t.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {t.change_pct >= 0 ? "+" : ""}{t.change_pct}%
              </span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono pt-1">
              Moving Avg: {t.moving_average} (Prev: {t.previous_value})
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrendCharts;
