import React from "react";

interface OperationalStatusCardProps {
  summary: Record<string, any>;
  ageHours: number;
  slaPct: number;
}

export const OperationalStatusCard: React.FC<OperationalStatusCardProps> = ({ summary, ageHours, slaPct }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="flex justify-between items-start border-b border-slate-800 pb-2">
        <div>
          <h2 className="text-base font-bold text-slate-100">{summary.title}</h2>
          <span className="font-mono text-cyan-400 text-xs">({summary.id})</span>
        </div>
        <span className="px-2.5 py-1 bg-slate-800 border border-slate-700 rounded font-mono text-xs text-amber-300 font-bold">
          {summary.priority} PRIORITY
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 bg-slate-800/50 p-3 rounded-lg border border-slate-700 text-xs">
        <div>
          <span className="text-slate-400 block text-[11px]">Case Status</span>
          <span className="font-semibold text-slate-200">{summary.status}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Case Age</span>
          <span className="font-semibold text-slate-200">{ageHours.toFixed(1)} hours</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">SLA Utilization</span>
          <span className={`font-semibold ${slaPct > 80 ? "text-rose-400" : "text-emerald-400"}`}>
            {slaPct}%
          </span>
        </div>
      </div>
    </div>
  );
};

export default OperationalStatusCard;
