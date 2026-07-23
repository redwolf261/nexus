import React from 'react';
import { ComplianceViolation } from './ViolationsTable';

interface RemediationPanelProps {
  violation: ComplianceViolation | null;
  onResolve?: (violationId: string) => void;
}

export const RemediationPanel: React.FC<RemediationPanelProps> = ({ violation, onResolve }) => {
  if (!violation) {
    return (
      <div className="p-6 text-center text-slate-500 border border-slate-800 rounded-lg bg-slate-900/40">
        Select a policy violation to view explicit evidence and remediation guidance.
      </div>
    );
  }

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-rose-400">Violation Details & Remediation</h3>
          <p className="text-[11px] text-slate-400">{violation.rule_name} ({violation.rule_id})</p>
        </div>
        <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-950 text-rose-400 border border-rose-800">
          {violation.severity}
        </span>
      </div>

      <div className="space-y-3">
        <div>
          <label className="text-[11px] font-semibold text-slate-400 uppercase">Violation Explanation</label>
          <p className="p-2.5 bg-slate-950 border border-slate-800 rounded text-slate-200 mt-1">
            {violation.explanation}
          </p>
        </div>

        <div>
          <label className="text-[11px] font-semibold text-cyan-400 uppercase">Step-by-Step Remediation Procedure</label>
          <p className="p-2.5 bg-slate-950 border border-slate-800 rounded text-emerald-300 mt-1">
            {violation.remediation}
          </p>
        </div>

        {violation.evidence && (
          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase">Evidence Snapshot</label>
            <pre className="p-2.5 bg-slate-950 border border-slate-800 rounded text-[11px] text-slate-300 overflow-x-auto mt-1">
              {JSON.stringify(violation.evidence, null, 2)}
            </pre>
          </div>
        )}

        {violation.legal_reference && (
          <div className="text-[11px] text-amber-400 font-semibold pt-1">
            Statutory & Legal Basis: {violation.legal_reference}
          </div>
        )}
      </div>

      <div className="pt-3 border-t border-slate-800 flex justify-end">
        <button
          onClick={() => onResolve && onResolve(violation.id)}
          className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold rounded text-xs transition-colors"
        >
          Mark Remediation Complete & Resolve
        </button>
      </div>
    </div>
  );
};
