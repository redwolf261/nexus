import React from "react";
import { TimelineEvent } from "./TimelinePanel";

interface RecentActivityProps {
  activity: TimelineEvent[];
}

export const RecentActivity: React.FC<RecentActivityProps> = ({ activity }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="border-b border-slate-800 pb-2">
        <h3 className="font-semibold text-slate-200">Recent Operational Activity Feed</h3>
      </div>
      <div className="space-y-2 max-h-[220px] overflow-y-auto">
        {activity?.map((act) => (
          <div key={act.event_id} className="p-2 bg-slate-800/40 rounded border border-slate-700/50 space-y-0.5">
            <div className="flex justify-between font-medium text-slate-200">
              <span>{act.title}</span>
              <span className="text-[10px] text-slate-400 font-mono">{act.actor}</span>
            </div>
            <p className="text-slate-400 text-[11px]">{act.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentActivity;
