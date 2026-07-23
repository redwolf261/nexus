import React from "react";

export interface AnalyticsReportDTO {
  total_notifications: int;
  delivery_success_rate: float;
  unread_rate: float;
  dismiss_rate: float;
  avg_ack_time_seconds: float;
  critical_avg_ack_time_seconds: float;
  channel_usage: Record<string, int>;
  district_stats: Record<string, any>;
  officer_engagement_score: float;
  supervisor_engagement_score: float;
}

interface NotificationAnalyticsProps {
  report: AnalyticsReportDTO | null;
  onRefresh?: () => void;
}

export const NotificationAnalytics: React.FC<NotificationAnalyticsProps> = ({
  report,
  onRefresh,
}) => {
  if (!report) {
    return (
      <div className="text-xs text-slate-500 py-8 text-center bg-slate-950/40 rounded-lg border border-slate-800 font-mono">
        Loading communication analytics...
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 font-mono text-xs shadow-xl">
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <span>Communication Metrics & Analytics</span>
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px]">
              Deterministic
            </span>
          </h3>
          <p className="text-[10px] text-slate-400 mt-0.5">
            Operational delivery rates, acknowledgement latencies, channel usage, and district engagement.
          </p>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 text-xs"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Metric Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
          <span className="text-[10px] text-slate-400">Delivery Success Rate</span>
          <div className="text-lg font-bold text-emerald-400">{report.delivery_success_rate}%</div>
        </div>

        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
          <span className="text-[10px] text-slate-400">Avg Ack Time</span>
          <div className="text-lg font-bold text-cyan-400">{report.avg_ack_time_seconds}s</div>
        </div>

        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
          <span className="text-[10px] text-slate-400">Critical Avg Ack</span>
          <div className="text-lg font-bold text-rose-400">{report.critical_avg_ack_time_seconds}s</div>
        </div>

        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
          <span className="text-[10px] text-slate-400">Officer Engagement</span>
          <div className="text-lg font-bold text-purple-400">{report.officer_engagement_score}%</div>
        </div>
      </div>

      {/* Channel usage breakdown */}
      <div className="space-y-2 pt-2 border-t border-slate-800">
        <h4 className="text-slate-300 font-bold text-[11px]">Channel Dispatch Breakdown</h4>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {Object.entries(report.channel_usage || {}).map(([ch, count]) => (
            <div key={ch} className="p-2 bg-slate-950 rounded border border-slate-800 text-center text-[10px]">
              <span className="text-slate-400 block">{ch}</span>
              <strong className="text-slate-200 text-sm">{count}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
