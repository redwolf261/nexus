import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getInvestigationWorkspace } from '@/lib/api';

export function useWorkspaceOrchestrator(id: string) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ['workspace', id],
    queryFn: async () => {
      const data = await getInvestigationWorkspace(id);
      qc.setQueryData(['workspace', 'meta', id], data.investigation);
      qc.setQueryData(['workspace', 'entities', id], data.entities);
      qc.setQueryData(['workspace', 'timeline', id], data.timeline);
      qc.setQueryData(['workspace', 'notes', id], data.notes);
      return data;
    },
    staleTime: Infinity,
  });
}

export function useWorkspaceMeta(id: string) {
  return useQuery({
    queryKey: ['workspace', 'meta', id],
    enabled: false,
  });
}

export function useWorkspaceEntities(id: string) {
  return useQuery({
    queryKey: ['workspace', 'entities', id],
    enabled: false,
  });
}

export function useWorkspaceTimeline(id: string) {
  return useQuery({
    queryKey: ['workspace', 'timeline', id],
    enabled: false,
  });
}

export function useWorkspaceNotes(id: string) {
  return useQuery({
    queryKey: ['workspace', 'notes', id],
    enabled: false,
  });
}
