import React from "react";

export interface IntelligenceItem {
  alert_id: string;
  alert_type: string;
  title: string;
  summary: string;
  confidence_score: number;
  affected_entities: string[];
  explainability_card_id: string;
  created_at: string;
}

export const IntelligenceFeed: React.FC<{ feed?: IntelligenceItem[]; onOpenExplainability?: (cardId: string) => void }> = ({
  feed,
  onOpenExplainability,
}) => {
  if (!feed || feed.length === 0) {
    return <div className="text-xs text-slate-500 py-4 text-center">No analytical intelligence alerts detected.</div>;
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-semibold text-slate-200 flex justify-between items-center">
        <span>Analytical Intelligence Feed (Phase 7 Outputs)</span>
        <span className="text-xs font-mono text-cyan-400">{feed.length} Active Feeds</span>
      </h3>

      <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
        {feed.map((item) => (
          <div key={item.alert_id} className="p-3 bg-slate-800/80 border border-slate-700 rounded-lg space-y-2 text-xs">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-bold text-slate-100">{item.title}</span>
                <div className="text-[11px] font-mono text-cyan-400">{item.alert_type}</div>
              </div>
              <span className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded text-[10px] font-mono">
                {(item.confidence_score * 100).toFixed(0)}% Confidence
              </span>
            </div>

            <p className="text-slate-300 text-[11px]">{item.summary}</p>

            <div className="flex justify-between items-center pt-1 border-t border-slate-800">
              <div className="text-[10px] text-slate-400 font-mono">
                Entities: {item.affected_entities.join(", ")}
              </div>
              <button
                onClick={() => onOpenExplainability && onOpenExplainability(item.explainability_card_id)}
                className="px-2.5 py-1 bg-cyan-900/60 hover:bg-cyan-800 text-cyan-200 border border-cyan-700/50 rounded text-[11px] font-medium"
              >
                Inspect Explainability Card ↗
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
