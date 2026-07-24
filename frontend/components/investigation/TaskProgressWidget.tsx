/**
 * Task Progress Widget — compact task status summary
 *
 * Displays:
 * - Completion percentage
 * - Task counts by status
 * - Visual indicators (bars, chips)
 * - Quick links to blocked/overdue
 */

import React, { useState, useEffect } from 'react';

interface TaskProgressData {
  total_tasks: number;
  status_breakdown: Record<string, number>;
  completed: number;
  percent_complete: number;
  blocked_tasks: any[];
  overdue_tasks: any[];
}

interface TaskProgressWidgetProps {
  investigationId: string;
  onNavigateToTasks?: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: 'bg-emerald-950 text-emerald-300 border-emerald-700',
  ACTIVE: 'bg-cyan-950 text-cyan-300 border-cyan-700',
  ASSIGNED: 'bg-indigo-950 text-indigo-300 border-indigo-700',
  BLOCKED: 'bg-rose-950 text-rose-300 border-rose-700',
  CANCELLED: 'bg-slate-800 text-slate-400 border-slate-700',
  SKIPPED: 'bg-amber-950 text-amber-400 border-amber-700',
  CREATED: 'bg-slate-900 text-slate-300 border-slate-700',
};

export const TaskProgressWidget: React.FC<TaskProgressWidgetProps> = ({
  investigationId,
  onNavigateToTasks,
}) => {
  const [progress, setProgress] = useState<TaskProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProgress = async () => {
      try {
        const res = await fetch(`/api/tasks/${investigationId}/progress`);
        if (!res.ok) throw new Error('Failed to load progress');
        const data = await res.json();
        setProgress(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    loadProgress();
    const interval = setInterval(loadProgress, 30000);
    return () => clearInterval(interval);
  }, [investigationId]);

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 animate-pulse">
        <div className="h-4 bg-slate-700 rounded w-1/2 mb-3" />
        <div className="h-2 bg-slate-700 rounded w-full mb-2" />
        <div className="h-2 bg-slate-700 rounded w-3/4" />
      </div>
    );
  }

  if (error || !progress) {
    return (
      <div className="bg-slate-900 border border-rose-900/60 rounded-xl p-4 text-xs text-rose-400 font-mono">
        {error || 'No task data available'}
      </div>
    );
  }

  const getBarColor = (percent: number) => {
    if (percent < 25) return 'bg-rose-500';
    if (percent < 75) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4 font-mono text-xs shadow-lg">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Task Progress</h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            {progress.completed}/{progress.total_tasks} completed
          </p>
        </div>
        <span className={`text-2xl font-bold font-mono ${
          progress.percent_complete >= 75 ? 'text-emerald-400' :
          progress.percent_complete >= 25 ? 'text-amber-400' : 'text-rose-400'
        }`}>
          {progress.percent_complete.toFixed(0)}%
        </span>
      </div>

      {/* Progress Bar */}
      <div>
        <div className="w-full bg-slate-800 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${getBarColor(progress.percent_complete)}`}
            style={{ width: `${Math.min(100, progress.percent_complete)}%` }}
          />
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="flex flex-wrap gap-1.5">
        {Object.entries(progress.status_breakdown)
          .filter(([_, count]) => count > 0)
          .map(([status, count]) => (
            <span
              key={status}
              className={`px-2 py-0.5 rounded border text-[10px] font-bold ${STATUS_COLORS[status] || 'bg-slate-800 text-slate-300 border-slate-700'}`}
            >
              {status}: {count}
            </span>
          ))}
      </div>

      {/* Alerts */}
      {progress.blocked_tasks.length > 0 && (
        <div className="flex items-center gap-2 p-2 bg-rose-950/30 border border-rose-800/50 rounded-lg text-rose-300">
          <span className="text-[10px]">⛔ {progress.blocked_tasks.length} blocked task{progress.blocked_tasks.length !== 1 ? 's' : ''}</span>
        </div>
      )}

      {progress.overdue_tasks.length > 0 && (
        <div className="flex items-center gap-2 p-2 bg-amber-950/30 border border-amber-800/50 rounded-lg text-amber-300">
          <span className="text-[10px]">⚠ {progress.overdue_tasks.length} overdue task{progress.overdue_tasks.length !== 1 ? 's' : ''}</span>
        </div>
      )}

      {onNavigateToTasks && (
        <button
          onClick={onNavigateToTasks}
          className="w-full py-1.5 text-[11px] text-slate-400 hover:text-slate-200 border border-slate-800 hover:border-slate-600 rounded-lg transition-colors"
        >
          View All Tasks →
        </button>
      )}
    </div>
  );
};

export default TaskProgressWidget;
