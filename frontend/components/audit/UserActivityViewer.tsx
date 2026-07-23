import React from 'react';
import { AuditEntry } from './AuditTimeline';

interface UserActivityViewerProps {
  entries: AuditEntry[];
  userId: string;
}

export const UserActivityViewer: React.FC<UserActivityViewerProps> = ({ entries, userId }) => {
  const userEntries = entries.filter((e) => e.actor_id === userId);

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="text-sm font-bold text-cyan-400">User Activity Stream: {userId}</h3>
        <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
          {userEntries.length} Actions Logged
        </span>
      </div>

      {userEntries.length === 0 ? (
        <div className="text-slate-500 text-center py-4">
          No recorded activity for user <span className="text-slate-300">{userId}</span>.
        </div>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
          {userEntries.map((item) => (
            <div key={item.id} className="p-2 bg-slate-950 border border-slate-800 rounded flex justify-between items-center">
              <div>
                <span className="text-cyan-400 font-semibold">{item.event_type}</span>
                <span className="text-slate-500 ml-2">({item.event_category})</span>
                {item.entity_type && (
                  <span className="text-slate-400 ml-2">
                    on {item.entity_type} #{item.entity_id}
                  </span>
                )}
              </div>
              <div className="text-[11px] text-slate-500">
                {new Date(item.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
