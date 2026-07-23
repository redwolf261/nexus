import React, { useState } from "react";

export interface TimelineEvent {
  event_id: str;
  timestamp: string;
  actor: string;
  event_type: string;
  category: string;
  title: string;
  description: string;
}

interface TimelinePanelProps {
  events: TimelineEvent[];
}

export const TimelinePanel: React.FC<TimelinePanelProps> = ({ events }) => {
  const [filterCategory, setFilterCategory] = useState<string>("ALL");

  const filtered = filterCategory === "ALL"
    ? events
    : events.filter((e) => e.category.toUpperCase() === filterCategory.toUpperCase());

  const getCategoryBadge = (cat: string) => {
    switch (cat.toUpperCase()) {
      case "ASSIGNMENT":
        return "bg-cyan-950 text-cyan-300 border-cyan-700";
      case "TASK":
        return "bg-emerald-950 text-emerald-300 border-emerald-700";
      case "ACTION":
        return "bg-indigo-950 text-indigo-300 border-indigo-700";
      case "EVIDENCE":
        return "bg-amber-950 text-amber-300 border-amber-700";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4 text-xs">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <h3 className="font-semibold text-slate-200">Unified Investigation Timeline ({filtered.length})</h3>
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-[11px]">Filter:</span>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs"
          >
            <option value="ALL">All Events</option>
            <option value="TASK">Tasks</option>
            <option value="ASSIGNMENT">Assignments</option>
            <option value="ACTION">Actions</option>
            <option value="EVIDENCE">Evidence</option>
          </select>
        </div>
      </div>

      <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
        {filtered.map((evt) => (
          <div key={evt.event_id} className="flex gap-3 text-xs border-l-2 border-slate-700 pl-3 py-1">
            <div className="flex-1 space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-100">{evt.title}</span>
                <span className={`px-1.5 py-0.5 rounded font-mono text-[9px] border ${getCategoryBadge(evt.category)}`}>
                  {evt.category}
                </span>
              </div>
              <p className="text-slate-300 text-[11px]">{evt.description}</p>
              <div className="flex justify-between text-[10px] text-slate-400 font-mono pt-1">
                <span>Actor: {evt.actor}</span>
                <span>{new Date(evt.timestamp).toLocaleString()}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelinePanel;
