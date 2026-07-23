import React from "react";

export interface HeatmapData {
  heatmap_type: string;
  district_scores: Record<string, number>;
  district_categories: Record<string, string>;
  matrix_data: any[];
}

interface HeatmapPanelProps {
  heatmaps: HeatmapData[];
}

export const HeatmapPanel: React.FC<HeatmapPanelProps> = ({ heatmaps }) => {
  const getCategoryColor = (cat: string) => {
    switch (cat.toUpperCase()) {
      case "CRITICAL":
        return "bg-rose-950 text-rose-300 border-rose-700";
      case "HIGH":
        return "bg-amber-950 text-amber-300 border-amber-700";
      case "MEDIUM":
        return "bg-sky-950 text-sky-300 border-sky-700";
      default:
        return "bg-emerald-950 text-emerald-300 border-emerald-700";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="border-b border-slate-800 pb-2">
        <h3 className="font-semibold text-slate-200">District Operational Risk & Backlog Heatmaps</h3>
      </div>
      <div className="space-y-4">
        {heatmaps?.map((hm, idx) => (
          <div key={idx} className="space-y-2">
            <span className="text-[11px] font-mono font-bold text-cyan-400">
              HEATMAP TYPE: {hm.heatmap_type}
            </span>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {Object.entries(hm.district_scores || {}).map(([distId, score]) => {
                const cat = hm.district_categories[distId] || "LOW";
                return (
                  <div
                    key={distId}
                    className={`p-2.5 rounded border text-center space-y-1 ${getCategoryColor(cat)}`}
                  >
                    <span className="block font-bold font-mono text-xs">{distId}</span>
                    <span className="block font-semibold">{score}</span>
                    <span className="block text-[9px] font-mono opacity-80">{cat}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HeatmapPanel;
