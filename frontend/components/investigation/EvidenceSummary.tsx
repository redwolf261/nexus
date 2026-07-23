import React from "react";

interface EvidenceSummaryProps {
  evidence: Record<string, any>;
}

export const EvidenceSummary: React.FC<EvidenceSummaryProps> = ({ evidence }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="border-b border-slate-800 pb-2">
        <h3 className="font-semibold text-slate-200">Evidence & Forensic Summary</h3>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-slate-800/60 p-2.5 rounded border border-slate-700">
          <span className="text-slate-400 block text-[11px]">Total Artifacts</span>
          <span className="text-base font-bold text-slate-100">{evidence.total_artifacts || 0}</span>
        </div>
        <div className="bg-slate-800/60 p-2.5 rounded border border-slate-700">
          <span className="text-slate-400 block text-[11px]">Chain of Custody</span>
          <span className="text-xs font-bold text-emerald-400">
            {evidence.chain_of_custody_verified ? "VERIFIED ✅" : "UNVERIFIED ⚠️"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default EvidenceSummary;
