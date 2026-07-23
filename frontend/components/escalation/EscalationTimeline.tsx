import React from "react";
import { EscalationBadge } from "./EscalationBadge";

export interface EscalationLevelDTO {
  level_order: number;
  authority_tier: string;
  role_name: string;
  timeout_hours: number;
  auto_escalate: bool;
}

interface EscalationTimelineProps {
  levels: EscalationLevelDTO[];
  currentLevelIndex: number;
  status: string;
}

export const EscalationTimeline: React.FC<EscalationTimelineProps> = ({
  levels,
  currentLevelIndex,
  status,
}) => {
  if (!levels || levels.length === 0) {
    return <div className="text-xs text-slate-500 py-2">No escalation chain defined.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Authority Tier Escalation Chain ({levels.length} Tiers)
        </h4>
        <EscalationBadge status={status} size="sm" />
      </div>

      <div className="relative pl-6 space-y-5 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {levels.map((lvl, idx) => {
          const isCurrent = idx === currentLevelIndex && status !== "RESOLVED";
          const isPassed = idx < currentLevelIndex || status === "RESOLVED";

          let dotColor = "bg-slate-800 border-slate-700 text-slate-400";
          if (isCurrent) {
            dotColor = "bg-rose-600 border-rose-500 text-white animate-pulse";
          } else if (isPassed) {
            dotColor = "bg-emerald-600 border-emerald-500 text-white";
          }

          return (
            <div key={lvl.level_order} className="relative">
              <span
                className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full border flex items-center justify-center text-[10px] font-bold font-mono ${dotColor}`}
              >
                {lvl.level_order}
              </span>

              <div
                className={`p-3 rounded-lg border text-xs transition-all ${
                  isCurrent
                    ? "bg-rose-950/20 border-rose-800/60 shadow-lg shadow-rose-950/20"
                    : isPassed
                    ? "bg-slate-900/80 border-slate-800"
                    : "bg-slate-900/40 border-slate-800/60 opacity-60"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">
                    Tier {lvl.level_order}: {lvl.authority_tier}
                  </span>
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                    Role: {lvl.role_name.toUpperCase()}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mt-2">
                  <span>SLA Timeout: {lvl.timeout_hours} Hours</span>
                  <span>Auto Escalate: {lvl.auto_escalate ? "YES" : "NO"}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
