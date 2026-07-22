/**
 * Investigation Tasks Panel — Task lifecycle and progress tracking
 *
 * Displays:
 * - Task list with status, priority, due dates
 * - Dependency graph visualization
 * - Progress bar and completion metrics
 * - Action buttons (assign, start, complete, cancel, skip, block)
 *
 * Blocks actions on dependent tasks (cannot start until dependencies complete).
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardHeader,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Button,
  ButtonGroup,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  Divider,
  Typography,
  Avatar,
  AvatarGroup,
} from '@mui/material';
import {
  Edit as EditIcon,
  PlayArrow as PlayIcon,
  Check as CompleteIcon,
  Close as CancelIcon,
  Block as BlockIcon,
  Skip as SkipIcon,
  PersonAdd as AssignIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

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

const TaskChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

const PriorityChip: React.FC<{ priority: string }> = ({ priority }) => {
  const colorMap: Record<string, 'error' | 'warning' | 'default' | 'info'> = {
    CRITICAL: 'error',
    HIGH: 'warning',
    MEDIUM: 'default',
    LOW: 'info',
  };
  return <TaskChip label={priority} size="small" color={colorMap[priority]} variant="outlined" />;
};

const StatusChip: React.FC<{ status: string; slaState?: string }> = ({ status, slaState }) => {
  const colorMap: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
    CREATED: 'default',
    ASSIGNED: 'primary',
    ACTIVE: 'info',
    BLOCKED: 'warning',
    COMPLETED: 'success',
    CANCELLED: 'error',
    SKIPPED: 'default',
  };

  let label = status;
  if (status === 'ACTIVE' && slaState === 'BREACHED') {
    label = 'SLA BREACHED';
    return <TaskChip label={label} size="small" color="error" variant="filled" />;
  } else if (status === 'ACTIVE' && slaState === 'WARNING') {
    label = 'WARNING';
    return <TaskChip label={label} size="small" color="warning" variant="filled" />;
  }

  return <TaskChip label={status} size="small" color={colorMap[status]} />;
};

interface InvestigationTasksPanelProps {
  investigationId: string;
  caseType?: string;
  onTaskCreated?: () => void;
}

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
    reason?: string;
  }>({
    open: false,
    action: '',
    task: null,
  });

  // Load tasks and progress
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

  // Initialize from template if case type provided
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

  // Execute task action
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
        const errData = await res.json();
        throw new Error(errData.detail || 'Action failed');
      }

      await loadTasks();
      setActionDialog({ open: false, action: '', task: null });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskAction = async (task: TaskData, action: string) => {
    // Finding 9 fix: Actually check dependencies from API
    if (action === 'start') {
      try {
        const depsRes = await fetch(`/api/tasks/${task.investigation_id}/dependencies`);
        if (!depsRes.ok) {
          setError('Failed to load dependencies');
          return;
        }
        const depData = await depsRes.json();

        // Find dependencies for this task
        const taskDeps = depData.dependencies.filter((d: any) => d.from === task.id);
        const unmetDeps = taskDeps.filter((d: any) => {
          const depTask = depData.tasks.find((t: any) => t.id === d.to);
          return depTask && depTask.status !== 'COMPLETED';
        });

        if (unmetDeps.length > 0) {
          setError(`Cannot start: ${unmetDeps.length} dependency(ies) not yet complete`);
          return;
        }
      } catch (err) {
        setError(`Failed to check dependencies: ${(err as Error).message}`);
        return;
      }
    }
    setActionDialog({ open: true, action, task, reason: '' });
  };

  // Get actionable tasks based on status
  const getAvailableActions = (task: TaskData): string[] => {
    switch (task.status) {
      case 'CREATED':
        return ['assign', 'cancel'];
      case 'ASSIGNED':
        return ['start', 'cancel', 'skip'];
      case 'ACTIVE':
        return ['complete', 'cancel', 'block', 'skip'];
      case 'BLOCKED':
        return ['unblock', 'cancel'];
      default:
        return [];
    }
  };

  if (loading && !tasks.length) return <CircularProgress />;

  return (
    <Box sx={{ p: 2 }}>
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Header with Initialize Button */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Investigation Tasks</Typography>
        {!tasks.length && caseType && (
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={initializeTemplate}
            disabled={loading}
          >
            Load Template
          </Button>
        )}
      </Box>

      {/* Progress Bar */}
      {progress && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">
                {progress.completed}/{progress.total_tasks} completed
              </Typography>
              <Typography variant="body2">{progress.percent_complete.toFixed(0)}%</Typography>
            </Box>
            <LinearProgress variant="determinate" value={progress.percent_complete} />

            {/* Status breakdown */}
            <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Object.entries(progress.status_breakdown).map(([status, count]) => (
                <Typography key={status} variant="caption">
                  {status}: {count}
                </Typography>
              ))}
            </Box>

            {/* Next due and blocked info */}
            {progress.next_due_task && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Next due: <strong>{progress.next_due_task.title}</strong> (
                {new Date(progress.next_due_task.due_at!).toLocaleDateString()})
              </Alert>
            )}

            {progress.blocked_tasks.length > 0 && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                {progress.blocked_tasks.length} task(s) blocked
              </Alert>
            )}

            {progress.overdue_tasks.length > 0 && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {progress.overdue_tasks.length} task(s) overdue
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Task List */}
      <Card>
        <CardHeader title="Task List" />
        <CardContent>
          {tasks.length === 0 ? (
            <Typography variant="body2" color="textSecondary">
              No tasks. Click "Load Template" to initialize from case type.
            </Typography>
          ) : (
            <List sx={{ width: '100%' }}>
              {tasks.map((task) => (
                <React.Fragment key={task.id}>
                  <ListItem
                    disablePadding
                    sx={{
                      bgcolor:
                        task.status === 'ACTIVE'
                          ? 'action.hover'
                          : task.status === 'COMPLETED'
                            ? 'action.selected'
                            : 'transparent',
                      mb: 1,
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                    }}
                  >
                    <ListItemButton
                      onClick={() => setSelectedTask(selectedTask?.id === task.id ? null : task)}
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle2">{task.title}</Typography>
                            <StatusChip status={task.status} slaState={task.sla_state} />
                            <PriorityChip priority={task.priority} />
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" display="block">
                              {task.description}
                            </Typography>
                            {task.due_at && (
                              <Typography variant="caption" display="block">
                                Due: {new Date(task.due_at).toLocaleDateString()}
                              </Typography>
                            )}
                            {task.assigned_officer_id && (
                              <Typography variant="caption" display="block">
                                Assigned to: {task.assigned_officer_id}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItemButton>

                    {/* Action Buttons */}
                    {selectedTask?.id === task.id && (
                      <Box sx={{ ml: 2, display: 'flex', gap: 0.5 }}>
                        {getAvailableActions(task).map((action) => {
                          const icons: Record<string, React.ReactNode> = {
                            assign: <AssignIcon fontSize="small" />,
                            start: <PlayIcon fontSize="small" />,
                            complete: <CompleteIcon fontSize="small" />,
                            cancel: <CancelIcon fontSize="small" />,
                            skip: <SkipIcon fontSize="small" />,
                            block: <BlockIcon fontSize="small" />,
                            unblock: <PlayIcon fontSize="small" />,
                          };

                          return (
                            <Button
                              key={action}
                              size="small"
                              startIcon={icons[action]}
                              onClick={() => handleTaskAction(task, action)}
                              disabled={loading}
                            >
                              {action}
                            </Button>
                          );
                        })}
                      </Box>
                    )}
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Action Dialog */}
      <Dialog
        open={actionDialog.open}
        onClose={() => setActionDialog({ open: false, action: '', task: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {actionDialog.action.charAt(0).toUpperCase() + actionDialog.action.slice(1)} Task
        </DialogTitle>
        <DialogContent>
          {actionDialog.task && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                <strong>Task:</strong> {actionDialog.task.title}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Current Status:</strong> {actionDialog.task.status}
              </Typography>

              {['block', 'complete', 'cancel', 'skip'].includes(actionDialog.action) && (
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label={
                    actionDialog.action === 'complete'
                      ? 'Completion Notes'
                      : 'Reason'
                  }
                  placeholder={
                    actionDialog.action === 'block'
                      ? 'What are you waiting for?'
                      : undefined
                  }
                  value={actionDialog.reason || ''}
                  onChange={(e) =>
                    setActionDialog({
                      ...actionDialog,
                      reason: e.target.value,
                    })
                  }
                  sx={{ mt: 2 }}
                />
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialog({ open: false, action: '', task: null })}>
            Cancel
          </Button>
          <Button
            onClick={() => {
              if (actionDialog.task) {
                executeAction(actionDialog.action, actionDialog.task, actionDialog.reason);
              }
            }}
            variant="contained"
            disabled={loading}
          >
            {actionDialog.action}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InvestigationTasksPanel;
