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
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  LinearProgress,
  Chip,
  Typography,
  Grid,
  Button,
  CircularProgress,
} from '@mui/material';
import { Block as BlockIcon, Warning as WarningIcon } from '@mui/icons-material';

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
    const interval = setInterval(loadProgress, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [investigationId]);

  if (loading) return <CircularProgress size={24} />;
  if (!progress) return null;

  const getProgressColor = (percent: number): 'success' | 'warning' | 'error' => {
    if (percent < 25) return 'error';
    if (percent < 75) return 'warning';
    return 'success';
  };

  return (
    <Card sx={{ bgcolor: 'background.paper' }}>
      <CardHeader
        title="Task Progress"
        subheader={`${progress.completed}/${progress.total_tasks} completed`}
      />
      <CardContent>
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Completion</Typography>
            <Typography variant="body2" fontWeight="bold">
              {progress.percent_complete.toFixed(0)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress.percent_complete}
            color={getProgressColor(progress.percent_complete)}
          />
        </Box>

        {/* Status breakdown */}
        <Grid container spacing={1} sx={{ mb: 2 }}>
          {Object.entries(progress.status_breakdown)
            .filter(([_, count]) => count > 0)
            .map(([status, count]) => (
              <Grid item key={status}>
                <Chip
                  label={`${status}: ${count}`}
                  size="small"
                  variant="outlined"
                  sx={{ opacity: 0.7 }}
                />
              </Grid>
            ))}
        </Grid>

        {/* Alerts */}
        {progress.blocked_tasks.length > 0 && (
          <Box
            sx={{
              p: 1,
              mb: 1,
              bgcolor: 'warning.light',
              borderRadius: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <BlockIcon fontSize="small" color="warning" />
            <Typography variant="caption">
              {progress.blocked_tasks.length} blocked
            </Typography>
          </Box>
        )}

        {progress.overdue_tasks.length > 0 && (
          <Box
            sx={{
              p: 1,
              mb: 1,
              bgcolor: 'error.light',
              borderRadius: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <WarningIcon fontSize="small" color="error" />
            <Typography variant="caption">
              {progress.overdue_tasks.length} overdue
            </Typography>
          </Box>
        )}

        {onNavigateToTasks && (
          <Button
            size="small"
            fullWidth
            variant="text"
            onClick={onNavigateToTasks}
            sx={{ mt: 1 }}
          >
            View All Tasks
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default TaskProgressWidget;
