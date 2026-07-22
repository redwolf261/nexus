import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';
import { applyEventReducer } from '@/lib/eventReducers';

export function useLiveWorkspace(caseId: string) {
  const qc = useQueryClient();
  const { lastMessage, isConnected } = useWebSocket(`case_${caseId}`);

  useEffect(() => {
    if (!lastMessage) return;
    
    // We received an event for this case
    console.log("[LiveWorkspace] Event received:", lastMessage.event_type);
    
    // Use deterministic event reducers instead of invalidating queries
    applyEventReducer(qc, lastMessage);
    
    // Intelligence panels can still be invalidated or we can add them to reducers
    if (lastMessage.event_type === "RISK_SCORE_CHANGED") {
      qc.invalidateQueries({ queryKey: ['caseRisk', caseId] });
    }
    
    if (lastMessage.event_type === "INTELLIGENCE_DISCOVERED") {
      qc.invalidateQueries({ queryKey: ['workspace', caseId] });
      qc.invalidateQueries({ queryKey: ['overlaps', caseId] });
      qc.invalidateQueries({ queryKey: ['recommendations', caseId] });
    }

  }, [lastMessage, caseId, qc]);

  return { isConnected };
}
