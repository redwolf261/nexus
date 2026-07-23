import React from 'react';

export interface ComplianceRule {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: string;
  enabled: boolean;
  version: number;
  policy_version: string;
  remediation: string;
  legal_reference?: string;
}

interface RuleViewerProps {
  rules: ComplianceRule[];
}

export const RuleViewer: React.FC<RuleViewerProps> = ({ rules }) => {
  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="text-sm font-bold text-cyan-400">Deterministic Policy Rule Catalog</h3>
        <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
          {rules.length} Rules Active
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-1">
        {rules.map((rule) => (
          <div key={rule.id} className="p-3 bg-slate-950 border border-slate-800 rounded space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold text-slate-100">{rule.name}</span>
                <div className="text-[10px] text-slate-500">{rule.id} | v{rule.policy_version}</div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-cyan-300 border border-slate-700">
                {rule.severity}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">{rule.description}</p>
            {rule.legal_reference && (
              <div className="text-[10px] text-amber-400 font-semibold">
                Reference: {rule.legal_reference}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
