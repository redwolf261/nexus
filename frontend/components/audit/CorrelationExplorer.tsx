import React from 'react';
import { AuditEntry } from './AuditTimeline';

interface CorrelationExplorerProps {
  entries: AuditEntry[];
  correlationId: string;
}

export const CorrelationExplorer: React.FC<CorrelationExplorerProps> = ({ entries, correlationId }) => {
  const correlated = entries.filter((e) => e.correlation_id === correlationId);

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="text-sm font-bold text-cyan-400">
          Cross-Subsystem Correlation Trace: {correlationId || 'N/A'}
        </h3>
        <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
          {correlated.length} Linked Events
        </span>
      </div>

      {correlated.length === 0 ? (
        <div className="text-slate-500 text-center py-4">
          No correlated audit events found for ID <span className="text-slate-300">{correlationId}</span>.
        </div>
      ) : (
        <div className="space-y-3">
          {correlated.map((step, idx) => (
            <div key={step.id} className="relative pl-6 border-l-2 border-cyan-500/50 pb-2">
              <div className="absolute -left-[17px] top-0.5 w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <div className="p-2 bg-slate-950 border border-slate-800 rounded">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-200">
                    Step {idx + 1}: {step.event_type}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {new Date(step.timestamp).toISOString()}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Category: {step.event_category} | Actor: {step.actor_id || 'System'} | Request ID: {step.request_id || 'Internal'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
