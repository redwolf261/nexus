import React, { useState } from 'react';

export interface AuditEntry {
  id: string;
  sequence: number;
  prev_hash: string;
  hash: string;
  timestamp: string;
  event_type: string;
  event_category: string;
  entity_type?: string;
  entity_id?: string;
  entity_version?: number;
  actor_id?: string;
  ip_address?: string;
  user_agent?: string;
  correlation_id?: string;
  request_id?: string;
  previous_state?: any;
  new_state?: any;
  payload?: any;
  retention_policy?: string;
}

interface AuditTimelineProps {
  entries: AuditEntry[];
  onSelectEntry?: (entry: AuditEntry) => void;
  isLoading?: boolean;
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({
  entries,
  onSelectEntry,
  isLoading = false,
}) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="p-6 text-center text-gray-400 animate-pulse">
        Loading Immutable Audit Ledger Timeline...
      </div>
    );
  }

  if (!entries || entries.length === 0) {
    return (
      <div className="p-6 text-center text-gray-400 border border-dashed border-gray-700 rounded-lg">
        No audit entries found matching current filter criteria.
      </div>
    );
  }

  return (
    <div className="space-y-4 font-mono text-sm">
      <div className="flex justify-between items-center px-4 py-2 bg-slate-900 border border-slate-800 rounded-md">
        <span className="text-xs text-cyan-400 font-semibold uppercase tracking-wider">
          Ledger Records: {entries.length}
        </span>
        <span className="text-xs text-slate-400">
          SHA-256 Verified Sequence Range: #{entries[entries.length - 1]?.sequence || 0} - #{entries[0]?.sequence || 0}
        </span>
      </div>

      <div className="relative border-l-2 border-slate-700 ml-4 pl-6 space-y-6">
        {entries.map((entry) => {
          const isSelected = selectedId === entry.id;
          return (
            <div
              key={entry.id}
              onClick={() => {
                setSelectedId(entry.id);
                if (onSelectEntry) onSelectEntry(entry);
              }}
              className={`relative cursor-pointer p-4 rounded-lg border transition-all duration-150 ${
                isSelected
                  ? 'bg-slate-800 border-cyan-500 shadow-md shadow-cyan-950'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
              }`}
            >
              {/* Timeline marker node */}
              <div
                className={`absolute -left-[31px] top-4 w-3.5 h-3.5 rounded-full border-2 ${
                  entry.event_category === 'AUTHENTICATION'
                    ? 'bg-amber-500 border-amber-300'
                    : entry.event_category === 'ESCALATION'
                    ? 'bg-rose-500 border-rose-300'
                    : entry.event_category === 'APPROVAL'
                    ? 'bg-emerald-500 border-emerald-300'
                    : 'bg-cyan-500 border-cyan-300'
                }`}
              />

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 text-xs font-bold rounded bg-slate-800 text-cyan-400 border border-slate-700">
                    #{entry.sequence}
                  </span>
                  <span className="font-semibold text-slate-100">{entry.event_type}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {entry.event_category}
                  </span>
                </div>
                <span className="text-xs text-slate-400">
                  {new Date(entry.timestamp).toLocaleString()}
                </span>
              </div>

              <div className="mt-2 text-xs text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
                {entry.entity_type && (
                  <span>
                    <strong className="text-slate-300">Entity:</strong> {entry.entity_type} ({entry.entity_id}) v{entry.entity_version}
                  </span>
                )}
                {entry.actor_id && (
                  <span>
                    <strong className="text-slate-300">Actor:</strong> {entry.actor_id}
                  </span>
                )}
                {entry.correlation_id && (
                  <span>
                    <strong className="text-slate-300">Correlation ID:</strong> {entry.correlation_id}
                  </span>
                )}
              </div>

              <div className="mt-2 text-[11px] font-mono text-slate-500 truncate">
                Hash: <span className="text-slate-400">{entry.hash}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
