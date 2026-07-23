import React, { useState } from 'react';

interface AuditSearchPanelProps {
  onSearch: (filters: {
    eventCategory?: string;
    entityType?: string;
    entityId?: string;
    actorId?: string;
    correlationId?: string;
  }) => void;
  onExport?: (format: 'json' | 'csv' | 'ndjson') => void;
  userRole?: string;
}

export const AuditSearchPanel: React.FC<AuditSearchPanelProps> = ({
  onSearch,
  onExport,
  userRole = 'ANALYST',
}) => {
  const [eventCategory, setEventCategory] = useState('');
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const [actorId, setActorId] = useState('');
  const [correlationId, setCorrelationId] = useState('');
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'ndjson'>('json');

  const canExport = ['ADMIN', 'SUPERVISOR', 'ACP', 'DCP'].includes(userRole.toUpperCase());

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      eventCategory: eventCategory || undefined,
      entityType: entityType || undefined,
      entityId: entityId || undefined,
      actorId: actorId || undefined,
      correlationId: correlationId || undefined,
    });
  };

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="text-sm font-bold text-slate-100">Audit Ledger Search & Controls</h3>
        <div className="flex items-center gap-2">
          {canExport && onExport && (
            <div className="flex items-center gap-1">
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as any)}
                className="bg-slate-950 border border-slate-700 text-slate-200 rounded px-2 py-1 text-xs"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="ndjson">NDJSON</option>
              </select>
              <button
                onClick={() => onExport(exportFormat)}
                className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded text-xs transition-colors"
              >
                Export Ledger
              </button>
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleApply} className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Category</label>
          <select
            value={eventCategory}
            onChange={(e) => setEventCategory(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
          >
            <option value="">All Categories</option>
            <option value="AUTHENTICATION">Authentication</option>
            <option value="TASK">Task</option>
            <option value="ASSIGNMENT">Assignment</option>
            <option value="GOVERNANCE">Governance</option>
            <option value="APPROVAL">Approval</option>
            <option value="ESCALATION">Escalation</option>
            <option value="NOTIFICATION">Notification</option>
            <option value="INVESTIGATION">Investigation</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Entity Type</label>
          <input
            type="text"
            placeholder="e.g. Task, Approval"
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
          />
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Entity ID</label>
          <input
            type="text"
            placeholder="e.g. TSK-1001"
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
          />
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Actor ID</label>
          <input
            type="text"
            placeholder="e.g. usr_123"
            value={actorId}
            onChange={(e) => setActorId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
          />
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Correlation ID</label>
          <input
            type="text"
            placeholder="e.g. corr_abc"
            value={correlationId}
            onChange={(e) => setCorrelationId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
          />
        </div>

        <div className="md:col-span-3 lg:col-span-5 flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={() => {
              setEventCategory('');
              setEntityType('');
              setEntityId('');
              setActorId('');
              setCorrelationId('');
              onSearch({});
            }}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs"
          >
            Reset Filters
          </button>
          <button
            type="submit"
            className="px-4 py-1 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded text-xs"
          >
            Apply Filters
          </button>
        </div>
      </form>
    </div>
  );
};
