import React from "react";

interface NotificationFiltersProps {
  category: string;
  onCategoryChange: (cat: string) => void;
  priority: string;
  onPriorityChange: (pr: string) => void;
  includeArchived: boolean;
  onIncludeArchivedChange: (val: boolean) => void;
}

export const NotificationFilters: React.FC<NotificationFiltersProps> = ({
  category,
  onCategoryChange,
  priority,
  onPriorityChange,
  includeArchived,
  onIncludeArchivedChange,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 font-mono text-xs shadow-lg">
      <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">Advanced Inbox Filters</h4>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-[10px] text-slate-400 mb-1">Source Category</label>
          <select
            value={category}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
          >
            <option value="ALL">All Categories</option>
            <option value="APPROVAL">Approvals</option>
            <option value="ESCALATION">Escalations</option>
            <option value="TASK">Tasks</option>
            <option value="CASE">Cases</option>
            <option value="INTELLIGENCE">Intelligence</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] text-slate-400 mb-1">Priority Level</label>
          <select
            value={priority}
            onChange={(e) => onPriorityChange(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>

        <div className="flex items-center pt-4">
          <label className="flex items-center gap-2 text-slate-300 text-xs cursor-pointer">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(e) => onIncludeArchivedChange(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-purple-600 focus:ring-0"
            />
            <span>Include Archived Items</span>
          </label>
        </div>
      </div>
    </div>
  );
};
