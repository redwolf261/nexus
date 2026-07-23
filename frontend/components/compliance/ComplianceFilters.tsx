import React, { useState } from 'react';

interface ComplianceFiltersProps {
  onSearch: (filters: { category?: string; severity?: string; districtId?: string }) => void;
  onExport?: (format: 'json' | 'csv' | 'ndjson') => void;
  canExport?: boolean;
}

export const ComplianceFilters: React.FC<ComplianceFiltersProps> = ({
  onSearch,
  onExport,
  canExport = true,
}) => {
  const [category, setCategory] = useState('');
  const [severity, setSeverity] = useState('');
  const [districtId, setDistrictId] = useState('');
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'ndjson'>('json');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      category: category || undefined,
      severity: severity || undefined,
      districtId: districtId || undefined,
    });
  };

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 space-y-3">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="text-sm font-bold text-slate-100">Compliance Filters & Export</h3>
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
              Export Report
            </button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Category</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
          >
            <option value="">All Categories</option>
            <option value="ASSIGNMENT">Assignment</option>
            <option value="APPROVAL">Approval</option>
            <option value="GOVERNANCE">Governance</option>
            <option value="ESCALATION">Escalation</option>
            <option value="NOTIFICATION">Notification</option>
            <option value="AUDIT">Audit</option>
            <option value="EVIDENCE">Evidence</option>
            <option value="AUTHENTICATION">Authentication</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Severity</label>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">District</label>
          <input
            type="text"
            placeholder="e.g. BANGALORE_CENTRAL"
            value={districtId}
            onChange={(e) => setDistrictId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
          />
        </div>

        <div className="md:col-span-3 flex justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={() => {
              setCategory('');
              setSeverity('');
              setDistrictId('');
              onSearch({});
            }}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs"
          >
            Reset
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
