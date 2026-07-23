import React from 'react';
import { AuditEntry } from './AuditTimeline';

interface EntityHistoryViewerProps {
  entry: AuditEntry | null;
}

export const EntityHistoryViewer: React.FC<EntityHistoryViewerProps> = ({ entry }) => {
  if (!entry) {
    return (
      <div className="p-6 text-center text-slate-500 border border-slate-800 rounded-lg bg-slate-900/40">
        Select an audit entry from the timeline to inspect version history and state diffs.
      </div>
    );
  }

  const prev = entry.previous_state;
  const curr = entry.new_state;

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg space-y-4 font-mono text-xs text-slate-200">
      <div className="flex justify-between items-center pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-cyan-400">
            Entity Audit Snapshot: {entry.entity_type || 'N/A'} ({entry.entity_id || 'N/A'})
          </h3>
          <p className="text-slate-400 text-[11px]">
            Event: {entry.event_type} | Version: #{entry.entity_version}
          </p>
        </div>
        <div className="text-right text-[11px] text-slate-400">
          <div>Actor: {entry.actor_id || 'System'}</div>
          <div>IP: {entry.ip_address || 'Internal'}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-xs font-semibold text-rose-400 mb-1">Previous State</div>
          <pre className="p-3 bg-slate-950 border border-slate-800 rounded overflow-x-auto text-[11px] text-slate-300">
            {prev ? JSON.stringify(prev, null, 2) : '// Initial state (Create operation)'}
          </pre>
        </div>
        <div>
          <div className="text-xs font-semibold text-emerald-400 mb-1">New State</div>
          <pre className="p-3 bg-slate-950 border border-slate-800 rounded overflow-x-auto text-[11px] text-slate-300">
            {curr ? JSON.stringify(curr, null, 2) : '// No state recorded'}
          </pre>
        </div>
      </div>

      <div>
        <div className="text-xs font-semibold text-cyan-400 mb-1">Event Payload & Metadata</div>
        <pre className="p-3 bg-slate-950 border border-slate-800 rounded overflow-x-auto text-[11px] text-slate-300">
          {entry.payload ? JSON.stringify(entry.payload, null, 2) : '{}'}
        </pre>
      </div>

      <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
        <span>Prev Hash: {entry.prev_hash}</span>
        <span>Curr Hash: {entry.hash}</span>
      </div>
    </div>
  );
};
