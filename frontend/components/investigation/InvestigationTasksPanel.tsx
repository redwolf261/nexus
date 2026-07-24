/**
 * Investigation Tasks Panel — Task lifecycle and progress tracking
 *
 * Displays:
 * - Task list with status, priority, due dates
 * - Progress bar and completion metrics
 * - Action buttons (assign, start, complete, cancel, skip, block)
 *
 * Blocks actions on dependent tasks (cannot start until dependencies complete).
 */

import React, { useState, useEffect } from 'react';

interface TaskData {
  id: string;
  investigation_id: string;
  title: string;
  description?: string;
  category: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'CREATED' | 'ASSIGNED' | 'ACTIVE' | 'BLOCKED' | 'COMPLETED' | 'CANCELLED' | 'SKIPPED';
  assigned_officer_id?: string;
  created_at: string;
  assigned_at?: string;
  started_at?: string;
  completed_at?: string;
  due_at?: string;
  sla_hours?: number;
  sla_state: 'NORMAL' | 'WARNING' | 'BREACHED';
  version: number;
}

interface TaskProgress {
  total_tasks: number;
  status_breakdown: Record<string, number>;
  completed: number;
  percent_complete: number;
  next_due_task?: TaskData;
  blocked_tasks: TaskData[];
  overdue_tasks: TaskData[];
}

interface InvestigationTasksPanelProps {
  investigationId: string;
  caseType?: string;
  onTaskCreated?: () => void;
}

const PRIORITY_STYLES: Record<string, string> = {
  CRITICAL: 'bg-rose-950 text-rose-300 border-rose-700',
  HIGH: 'bg-amber-950 text-amber-300 border-amber-700',
  MEDIUM: 'bg-cyan-950 text-cyan-300 border-cyan-700',
  LOW: 'bg-slate-800 text-slate-400 border-slate-700',
};

const STATUS_STYLES: Record<string, string> = {
  CREATED: 'bg-slate-800 text-slate-300 border-slate-600',
  ASSIGNED: 'bg-indigo-950 text-indigo-300 border-indigo-700',
  ACTIVE: 'bg-cyan-950 text-cyan-300 border-cyan-700',
  BLOCKED: 'bg-amber-950 text-amber-300 border-amber-700',
  COMPLETED: 'bg-emerald-950 text-emerald-300 border-emerald-700',
  CANCELLED: 'bg-slate-900 text-slate-500 border-slate-700',
  SKIPPED: 'bg-slate-900 text-slate-400 border-slate-700',
};

export const InvestigationTasksPanel: React.FC<InvestigationTasksPanelProps> = ({
  investigationId,
  caseType,
  onTaskCreated,
}) => {
  const [tasks, setTasks] = useState<TaskData[]>([]);
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<TaskData | null>(null);
  const [actionDialog, setActionDialog] = useState<{
    open: boolean;
    action: string;
    task: TaskData | null;
    reason: string;
  }>({ open: false, action: '', task: null, reason: '' });

  const loadTasks = async () => {
    setLoading(true);
    try {
      const tasksRes = await fetch(
        `/api/tasks/investigation/${investigationId}?include_completed=true`
      );
      if (!tasksRes.ok) throw new Error('Failed to load tasks');
      const tasksData = await tasksRes.json();
      setTasks(tasksData);

      const progressRes = await fetch(`/api/tasks/${investigationId}/progress`);
      if (progressRes.ok) {
        const progressData = await progressRes.json();
        setProgress(progressData);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [investigationId]);

  const initializeTemplate = async () => {
    if (!caseType) return;
    setLoading(true);
    try {
      const res = await fetch(
        `/api/tasks/${investigationId}/initialize-from-template/${caseType}`,
        { method: 'POST' }
      );
      if (!res.ok) throw new Error('Failed to initialize template');
      await loadTasks();
      onTaskCreated?.();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const executeAction = async (action: string, task: TaskData, reason?: string) => {
    setLoading(true);
    try {
      const payload: any = { version: task.version };
      if (reason) payload.reason = reason;
      if (action === 'complete') payload.completion_notes = reason;

      const res = await fetch(`/api/tasks/${task.id}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Action failed');
      }
      setActionDialog({ open: false, action: '', task: null, reason: '' });
      await loadTasks();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const openActionDialog = (action: string, task: TaskData) => {
    setActionDialog({ open: true, action, task, reason: '' });
  };

  const closeActionDialog = () => {
    setActionDialog({ open: false, action: '', task: null, reason: '' });
  };

  const confirmAction = () => {
    if (actionDialog.task) {
      executeAction(actionDialog.action, actionDialog.task, actionDialog.reason);
    }
  };

  const canStart = (task: TaskData) =>
    task.status === 'ASSIGNED' && task.sla_state !== 'BREACHED';

  const getActionButtons = (task: TaskData) => {
    const buttons: { label: string; action: string; style: string }[] = [];
    switch (task.status) {
      case 'ASSIGNED':
        buttons.push({ label: 'Start', action: 'start', style: 'bg-cyan-700 hover:bg-cyan-600 text-white' });
        buttons.push({ label: 'Block', action: 'block', style: 'bg-amber-700 hover:bg-amber-600 text-white' });
        buttons.push({ label: 'Cancel', action: 'cancel', style: 'bg-slate-700 hover:bg-slate-600 text-slate-200' });
        break;
      case 'ACTIVE':
        buttons.push({ label: 'Complete', action: 'complete', style: 'bg-emerald-700 hover:bg-emerald-600 text-white' });
        buttons.push({ label: 'Block', action: 'block', style: 'bg-amber-700 hover:bg-amber-600 text-white' });
        buttons.push({ label: 'Skip', action: 'skip', style: 'bg-slate-700 hover:bg-slate-600 text-slate-200' });
        break;
      case 'BLOCKED':
        buttons.push({ label: 'Unblock', action: 'unblock', style: 'bg-indigo-700 hover:bg-indigo-600 text-white' });
        buttons.push({ label: 'Cancel', action: 'cancel', style: 'bg-slate-700 hover:bg-slate-600 text-slate-200' });
        break;
      case 'CREATED':
        buttons.push({ label: 'Cancel', action: 'cancel', style: 'bg-slate-700 hover:bg-slate-600 text-slate-200' });
        break;
    }
    return buttons;
  };

  const ACTIONS_NEEDING_REASON = ['block', 'cancel', 'complete', 'skip'];

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString();
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl font-mono text-xs shadow-xl">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex justify-between items-center">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            Investigation Tasks
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px]">
              {tasks.length} tasks
            </span>
          </h3>
          {progress && (
            <p className="text-[11px] text-slate-400 mt-0.5">
              {progress.completed}/{progress.total_tasks} completed &bull; {progress.percent_complete.toFixed(0)}%
            </p>
          )}
        </div>

        <div className="flex gap-2">
          {caseType && tasks.length === 0 && (
            <button
              onClick={initializeTemplate}
              disabled={loading}
              className="px-3 py-1.5 bg-purple-700 hover:bg-purple-600 text-white rounded-lg text-xs font-semibold shadow"
            >
              Init from Template
            </button>
          )}
          <button
            onClick={loadTasks}
            disabled={loading}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 text-xs"
          >
            {loading ? '...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {progress && (
        <div className="px-4 pt-3 pb-1">
          <div className="w-full bg-slate-800 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all duration-700 ${
                progress.percent_complete >= 75 ? 'bg-emerald-500' :
                progress.percent_complete >= 25 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${Math.min(100, progress.percent_complete)}%` }}
            />
          </div>
          {/* Status Breakdown */}
          <div className="flex flex-wrap gap-1.5 mt-2">
            {Object.entries(progress.status_breakdown)
              .filter(([, count]) => count > 0)
              .map(([status, count]) => (
                <span
                  key={status}
                  className={`px-1.5 py-0.5 rounded border text-[9px] font-bold ${STATUS_STYLES[status] || 'bg-slate-800 text-slate-300 border-slate-700'}`}
                >
                  {status}: {count}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mx-4 mt-2 p-2 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-[11px]">
          {error}
          <button className="ml-2 underline" onClick={() => setError(null)}>dismiss</button>
        </div>
      )}

      {/* Task List */}
      <div className="p-4 space-y-2 max-h-[600px] overflow-y-auto">
        {loading && tasks.length === 0 ? (
          <div className="text-slate-500 py-8 text-center animate-pulse">Loading tasks...</div>
        ) : tasks.length === 0 ? (
          <div className="text-slate-500 py-8 text-center border border-dashed border-slate-800 rounded-lg italic">
            No tasks created yet.
            {caseType && (
              <button
                onClick={initializeTemplate}
                className="block mx-auto mt-3 px-4 py-1.5 bg-purple-800 hover:bg-purple-700 text-white rounded-lg text-xs"
              >
                Initialize from {caseType} Template
              </button>
            )}
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              onClick={() => setSelectedTask(selectedTask?.id === task.id ? null : task)}
              className={`p-3 rounded-lg border transition-all cursor-pointer ${
                selectedTask?.id === task.id
                  ? 'bg-slate-800 border-cyan-700'
                  : 'bg-slate-900/80 border-slate-800 hover:border-slate-600'
              } ${task.status === 'COMPLETED' ? 'opacity-60' : ''}`}
            >
              {/* Task Row */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-slate-100 truncate">{task.title}</span>
                    {task.sla_state === 'BREACHED' && (
                      <span className="px-1.5 py-0.5 rounded bg-rose-900 text-rose-300 border border-rose-700 text-[9px] animate-pulse font-bold">
                        SLA BREACHED
                      </span>
                    )}
                    {task.sla_state === 'WARNING' && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-900 text-amber-300 border border-amber-700 text-[9px] font-bold">
                        SLA WARNING
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-400">
                    <span>{task.category}</span>
                    {task.assigned_officer_id && <span>&bull; {task.assigned_officer_id}</span>}
                    {task.due_at && <span>&bull; Due: {formatDate(task.due_at)}</span>}
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <span className={`px-1.5 py-0.5 rounded border text-[9px] font-bold ${PRIORITY_STYLES[task.priority]}`}>
                    {task.priority}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded border text-[9px] font-bold ${STATUS_STYLES[task.status]}`}>
                    {task.status}
                  </span>
                </div>
              </div>

              {/* Expanded Actions */}
              {selectedTask?.id === task.id && (
                <div
                  className="mt-3 pt-3 border-t border-slate-700 space-y-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  {task.description && (
                    <p className="text-slate-300 text-[11px] leading-relaxed">{task.description}</p>
                  )}
                  <div className="flex flex-wrap gap-1.5">
                    {getActionButtons(task).map(({ label, action, style }) => (
                      <button
                        key={action}
                        onClick={() => {
                          if (ACTIONS_NEEDING_REASON.includes(action)) {
                            openActionDialog(action, task);
                          } else {
                            executeAction(action, task);
                          }
                        }}
                        disabled={loading}
                        className={`px-3 py-1 rounded text-[10px] font-semibold ${style} disabled:opacity-50`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Action Confirmation Dialog */}
      {actionDialog.open && actionDialog.task && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-sm font-bold text-slate-100 mb-1 capitalize">
              {actionDialog.action} Task
            </h3>
            <p className="text-[11px] text-slate-400 mb-4">
              Task: <span className="text-slate-200">{actionDialog.task.title}</span>
            </p>

            {ACTIONS_NEEDING_REASON.includes(actionDialog.action) && (
              <textarea
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-xs resize-none focus:outline-none focus:ring-1 focus:ring-cyan-600 mb-4"
                rows={3}
                placeholder={
                  actionDialog.action === 'complete'
                    ? 'Completion notes (optional)...'
                    : `Reason for ${actionDialog.action}...`
                }
                value={actionDialog.reason}
                onChange={(e) => setActionDialog((prev) => ({ ...prev, reason: e.target.value }))}
              />
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={closeActionDialog}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
              >
                Cancel
              </button>
              <button
                onClick={confirmAction}
                disabled={loading}
                className="px-4 py-1.5 bg-cyan-700 hover:bg-cyan-600 text-white rounded-lg text-xs font-semibold shadow"
              >
                {loading ? 'Processing...' : `Confirm ${actionDialog.action}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvestigationTasksPanel;
