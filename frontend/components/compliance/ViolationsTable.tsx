import React from 'react';

export interface ComplianceViolation {
  id: string;
  rule_id: string;
  rule_name: string;
  category: string;
  severity: string;
  violated_entity_type?: string;
  violated_entity_id?: string;
  actor_id?: string;
  district_id?: string;
  explanation: string;
  evidence?: any;
  remediation: string;
  legal_reference?: string;
  resolved: boolean;
  timestamp: string;
}

interface ViolationsTableProps {
  violations: ComplianceViolation[];
  onSelectViolation?: (violation: ComplianceViolation) => void;
  isLoading?: boolean;
}

export const ViolationsTable: React.FC<ViolationsTableProps> = ({
  violations,
  onSelectViolation,
  isLoading = false,
}) => {
  if (isLoading) {
    return <div className="p-6 text-center text-slate-400 animate-pulse">Loading compliance violations...</div>;
  }

  if (!violations || violations.length === 0) {
    return (
      <div className="p-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-lg">
        ✅ Zero active policy violations detected. Subsystem fully compliant.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto border border-slate-800 rounded-lg font-mono text-xs text-slate-200 bg-slate-900">
      <table className="w-full text-left border-collapse">
        <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase text-[11px]">
          <tr>
            <th className="p-3">Severity</th>
            <th className="p-3">Rule Name</th>
            <th className="p-3">Category</th>
            <th className="p-3">Violated Entity</th>
            <th className="p-3">Actor</th>
            <th className="p-3">District</th>
            <th className="p-3">Timestamp</th>
            <th className="p-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {violations.map((v) => {
            const isCrit = v.severity === 'CRITICAL';
            const isHigh = v.severity === 'HIGH';

            return (
              <tr
                key={v.id}
                onClick={() => onSelectViolation && onSelectViolation(v)}
                className="hover:bg-slate-800/60 cursor-pointer transition-colors"
              >
                <td className="p-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      isCrit
                        ? 'bg-rose-950 text-rose-400 border-rose-800'
                        : isHigh
                        ? 'bg-amber-950 text-amber-400 border-amber-800'
                        : 'bg-slate-800 text-slate-300 border-slate-700'
                    }`}
                  >
                    {v.severity}
                  </span>
                </td>
                <td className="p-3 font-semibold text-slate-100">{v.rule_name}</td>
                <td className="p-3 text-slate-400">{v.category}</td>
                <td className="p-3 text-cyan-400">
                  {v.violated_entity_type || 'N/A'}: {v.violated_entity_id || 'N/A'}
                </td>
                <td className="p-3 text-slate-300">{v.actor_id || 'System'}</td>
                <td className="p-3 text-slate-400">{v.district_id || 'CENTRAL'}</td>
                <td className="p-3 text-slate-500">{new Date(v.timestamp).toLocaleString()}</td>
                <td className="p-3 text-right">
                  <button className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded text-[10px]">
                    Inspect & Remediate
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
