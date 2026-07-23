import React from 'react';

interface ComplianceTimelineProps {
  trend7d: { date: string; score: number }[];
  trend30d: { date: string; score: number }[];
}

export const ComplianceTimeline: React.FC<ComplianceTimelineProps> = ({ trend7d, trend30d }) => {
  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="text-sm font-bold text-slate-100">Historical Compliance Trend Timeline</h3>
        <span className="text-xs text-cyan-400">7-Day & 30-Day Score Moving Average</span>
      </div>

      <div className="space-y-2">
        <div className="text-xs text-slate-400 font-semibold mb-1">7-Day Moving Trend</div>
        <div className="grid grid-cols-7 gap-2">
          {trend7d.map((point) => (
            <div key={point.date} className="p-2 bg-slate-950 border border-slate-800 rounded text-center">
              <div className="text-[10px] text-slate-500">{point.date.slice(5)}</div>
              <div className="text-xs font-bold text-emerald-400 mt-1">{point.score.toFixed(1)}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
