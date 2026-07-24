import React, { useState } from "react";

export interface DigestContentDTO {
  digest_id: string;
  digest_type: string;
  recipient_id: string;
  recipient_role: string;
  generated_at: string;
  unread_notifications_count: number;
  critical_alerts_count: number;
  pending_approvals_count: number;
  escalations_count: number;
  summary_text: string;
}

interface DigestPanelProps {
  onGenerateDigest: (digestType: string) => Promise<DigestContentDTO>;
  latestDigest?: DigestContentDTO | null;
}

export const DigestPanel: React.FC<DigestPanelProps> = ({
  onGenerateDigest,
  latestDigest,
}) => {
  const [digestType, setDigestType] = useState("MORNING_DIGEST");
  const [currentDigest, setCurrentDigest] = useState<DigestContentDTO | null>(latestDigest || null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await onGenerateDigest(digestType);
      setCurrentDigest(res);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 font-mono text-xs shadow-xl">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <span>Deterministic Digest Generator</span>
            <span className="px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 text-[10px]">
              Reproducible Summary
            </span>
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Generates role-specific operational digests summarizing unread alerts, escalations, and approvals.
          </p>
        </div>

        <div className="flex gap-2 w-full sm:w-auto">
          <select
            value={digestType}
            onChange={(e) => setDigestType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 text-xs"
          >
            <option value="MORNING_DIGEST">Morning Digest</option>
            <option value="EVENING_DIGEST">Evening Digest</option>
            <option value="SHIFT_DIGEST">Shift Digest</option>
            <option value="DAILY_SUMMARY">Daily Summary</option>
            <option value="WEEKLY_SUMMARY">Weekly Summary</option>
            <option value="SUPERVISOR_DIGEST">Supervisor Digest</option>
            <option value="ACP_DIGEST">ACP Digest</option>
            <option value="DCP_DIGEST">DCP Digest</option>
          </select>

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-lg shadow whitespace-nowrap"
          >
            {isGenerating ? "Generating..." : "Generate Digest"}
          </button>
        </div>
      </div>

      {currentDigest ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400">Unread Alerts</span>
              <div className="text-base font-bold text-purple-400">{currentDigest.unread_notifications_count}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400">Critical Alerts</span>
              <div className="text-base font-bold text-rose-400">{currentDigest.critical_alerts_count}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400">Pending Approvals</span>
              <div className="text-base font-bold text-cyan-400">{currentDigest.pending_approvals_count}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400">Active Escalations</span>
              <div className="text-base font-bold text-amber-400">{currentDigest.escalations_count}</div>
            </div>
          </div>

          <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 text-[11px] overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {currentDigest.summary_text}
          </pre>
        </div>
      ) : (
        <div className="text-xs text-slate-500 py-6 text-center bg-slate-950/40 rounded-lg border border-slate-800 italic">
          Select digest type and click Generate Digest to view operational summary.
        </div>
      )}
    </div>
  );
};
