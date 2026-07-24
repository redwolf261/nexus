import { QueryClient } from '@tanstack/react-query';

export const applyEventReducer = (qc: QueryClient, event: any) => {
  const { event_type, payload, case_id } = event;
  if (!case_id) return;

  const timestamp = event.timestamp || new Date().toISOString();

  // Helper to add timeline event
  const addTimelineEvent = (type: string, desc: string, entity_id: string | null = null) => {
    qc.setQueryData(['workspace', 'timeline', case_id], (old: any) => {
      if (!old) return old;
      return [{ type, event_type, description: desc, date: timestamp, entity_id }, ...old];
    });
  };

  switch (event_type) {
    case 'ENTITY_ATTACHED': {
      qc.setQueryData(['workspace', 'entities', case_id], (old: any) => {
        if (!old) return old;
        const exists = old.some((e: any) => e.entity_id === payload.entity_id && e.entity_type === payload.entity_type);
        if (exists) return old;
        return [...old, { entity_type: payload.entity_type, entity_id: payload.entity_id, details: payload.details || {} }];
      });
      addTimelineEvent('ENTITY_LINKED', `Linked ${payload.entity_type}: ${payload.entity_id}`, payload.entity_id);
      break;
    }
    case 'ENTITY_DETACHED': {
      qc.setQueryData(['workspace', 'entities', case_id], (old: any) => {
        if (!old) return old;
        return old.filter((e: any) => !(e.entity_id === payload.entity_id && e.entity_type === payload.entity_type));
      });
      addTimelineEvent('ENTITY_UNLINKED', `Unlinked ${payload.entity_type}: ${payload.entity_id}`, payload.entity_id);
      break;
    }
    case 'NOTE_ADDED': {
      qc.setQueryData(['workspace', 'notes', case_id], (old: any) => {
        if (!old) return old;
        return [payload.note, ...old];
      });
      addTimelineEvent('NOTE_ADDED', `Note added by ${payload.note?.author || 'system'}`);
      break;
    }
    case 'CASE_STATUS_CHANGED': {
      qc.setQueryData(['workspace', 'meta', case_id], (old: any) => {
        if (!old) return old;
        return { ...old, status: payload.new_status };
      });
      addTimelineEvent('STATUS_CHANGED', `Status changed to ${payload.new_status}`);
      break;
    }
    case 'CASE_PRIORITY_CHANGED': {
      qc.setQueryData(['workspace', 'meta', case_id], (old: any) => {
        if (!old) return old;
        return { ...old, priority: payload.new_priority };
      });
      addTimelineEvent('PRIORITY_CHANGED', `Priority changed to ${payload.new_priority}`);
      break;
    }
    default:
      break;
  }
};
