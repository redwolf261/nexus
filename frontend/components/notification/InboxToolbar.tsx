import React from "react";

interface InboxToolbarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  category: string;
  onCategoryChange: (cat: string) => void;
  priority: string;
  onPriorityChange: (pr: string) => void;
  selectedCount: number;
  onOpenBulkModal: () => void;
  onRefresh: () => void;
}

export const InboxToolbar: React.FC<InboxToolbarProps> = ({
  searchQuery,
  onSearchChange,
  category,
  onCategoryChange,
  priority,
  onPriorityChange,
  selectedCount,
  onOpenBulkModal,
  onRefresh,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
      <div className="flex items-center gap-2 flex-1 min-w-[220px]">
        <input
          type="text"
          placeholder="Search notifications..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 w-full focus:outline-none focus:border-purple-500"
        />
      </div>

      <div className="flex items-center gap-2">
        <select
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none"
        >
          <option value="ALL">All Categories</option>
          <option value="APPROVAL">Approvals</option>
          <option value="ESCALATION">Escalations</option>
          <option value="TASK">Tasks</option>
          <option value="CASE">Cases</option>
          <option value="INTELLIGENCE">Intelligence</option>
        </select>

        <select
          value={priority}
          onChange={(e) => onPriorityChange(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none"
        >
          <option value="ALL">All Priorities</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>

        {selectedCount > 0 && (
          <button
            onClick={onOpenBulkModal}
            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold shadow flex items-center gap-1"
          >
            <span>Bulk Actions ({selectedCount})</span>
          </button>
        )}

        <button
          onClick={onRefresh}
          className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700"
        >
          Refresh
        </button>
      </div>
    </div>
  );
};
