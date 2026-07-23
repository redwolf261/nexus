import React from "react";

export interface Recommendation {
  recommendation_id: string;
  rule_code: str;
  reason: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
  recommended_action: string;
  supporting_evidence: string[];
  confidence_score: number;
}

interface DecisionSupportPanelProps {
  recommendations: Recommendation[];
  onActionClick?: (rec: Recommendation) => void;
}

export const DecisionSupportPanel: React.FC<DecisionSupportPanelProps> = ({ recommendations, onActionClick }) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs text-slate-400">
        No active decision recommendations. Operational metrics within healthy thresholds.
      </div>
    );
  }

  const getPriorityBadge = (prio: string) => {
    switch (prio.toUpperCase()) {
      case "CRITICAL":
        return "bg-rose-950 text-rose-300 border-rose-700";
      case "HIGH":
        return "bg-amber-950 text-amber-300 border-amber-700";
      case "MEDIUM":
        return "bg-sky-950 text-sky-300 border-sky-700";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <h3 className="font-semibold text-slate-200">Supervisor Decision Support ({recommendations.length})</h3>
        <span className="text-[11px] text-cyan-400 font-mono">Rule-Based Engine</span>
      </div>

      <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
        {recommendations.map((r) => (
          <div key={r.recommendation_id} className="p-3 bg-slate-800/70 border border-slate-700 rounded-lg space-y-1.5">
            <div className="flex justify-between items-start">
              <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] border ${getPriorityBadge(r.priority)}`}>
                [{r.rule_code}] {r.priority}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">Conf: {(r.confidence_score * 100).toFixed(0)}%</span>
            </div>

            <p className="text-slate-200 text-xs">{r.reason}</p>

            <div className="bg-slate-900/60 p-2 rounded border border-slate-800 text-[11px] text-emerald-300 font-medium">
              Action Suggestion: {r.recommended_action}
            </div>

            {r.supporting_evidence && r.supporting_evidence.length > 0 && (
              <div className="text-[10px] text-slate-400">
                Evidence: {r.supporting_evidence.join(" | ")}
              </div>
            )}

            {onActionClick && (
              <button
                onClick={() => onActionClick(r)}
                className="mt-1 text-[11px] px-2.5 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700 rounded font-medium transition-colors"
              >
                Apply Recommendation
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DecisionSupportPanel;
