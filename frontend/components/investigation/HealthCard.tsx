import React from "react";

export interface CaseHealth {
  investigation_id: string;
  score: number;
  category: "HEALTHY" | "MONITOR" | "ATTENTION" | "CRITICAL" | string;
  factor_scores: Record<string, number>;
  explanations: string[];
  calculated_at: string;
}

interface HealthCardProps {
  health: CaseHealth;
}

export const HealthCard: React.FC<HealthCardProps> = ({ health }) => {
  const getCategoryColor = (cat: string) => {
    switch (cat.toUpperCase()) {
      case "HEALTHY":
        return "text-emerald-400 border-emerald-600 bg-emerald-950/40";
      case "MONITOR":
        return "text-sky-400 border-sky-600 bg-sky-950/40";
      case "ATTENTION":
        return "text-amber-400 border-amber-600 bg-amber-950/40";
      default:
        return "text-rose-400 border-rose-600 bg-rose-950/40";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <h3 className="font-semibold text-slate-200">Operational Case Health</h3>
        <span className={`px-2 py-0.5 rounded font-mono font-bold border ${getCategoryColor(health.category)}`}>
          {health.category} ({health.score}/100)
        </span>
      </div>

      <div className="space-y-1.5">
        <div className="flex justify-between text-[11px] text-slate-400">
          <span>Overall Health Index</span>
          <span className="font-bold text-slate-200">{health.score}%</span>
        </div>
        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              health.score >= 80
                ? "bg-emerald-500"
                : health.score >= 60
                ? "bg-sky-500"
                : health.score >= 40
                ? "bg-amber-500"
                : "bg-rose-500"
            }`}
            style={{ width: `${health.score}%` }}
          />
        </div>
      </div>

      <div className="pt-2 border-t border-slate-800/60 space-y-1">
        <span className="text-[11px] font-medium text-slate-400">Health Factors & Audit Rationale:</span>
        <ul className="list-disc list-inside text-[11px] text-slate-300 space-y-0.5">
          {health.explanations?.map((exp, idx) => (
            <li key={idx}>{exp}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default HealthCard;
