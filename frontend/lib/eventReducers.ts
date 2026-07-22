
import { QueryClient } from ''@tanstack/react-query'';

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
    case ''ENTITY_ATTACHED'': {
      qc.setQueryData(['workspace', 'entities', case_id], (old: any) => {
        if (!old) return old;
        const newEntities = { ...old };
        const typeKey = payload.entity_type;
        if (!newEntities[typeKey]) newEntities[typeKey] = [];
        
        // Prevent duplicate entity rendering
        const exists = newEntities[typeKey].find((e: any) => 
            (e.id || e.fir_id || e.citizen_id || e.vehicle_id || e.phone_id || e.criminal_id) === payload.entity_id
        );
        
        if (!exists) {
            newEntities[typeKey] = [...newEntities[typeKey], { id: payload.entity_id }];
        }
        return newEntities;
      });
      addTimelineEvent(''Intelligence'', Entity  () attached., payload.entity_id);
      break;
    }
    
    case ''ENTITY_REMOVED'': {
      qc.setQueryData(['workspace', 'entities', case_id], (old: any) => {
        if (!old) return old;
        const newEntities = { ...old };
        const typeKey = payload.entity_type;
        if (newEntities[typeKey]) {
            newEntities[typeKey] = newEntities[typeKey].filter((e: any) => 
                (e.id || e.fir_id || e.citizen_id || e.vehicle_id || e.phone_id || e.criminal_id) !== payload.entity_id
            );
        }
        return newEntities;
      });
      addTimelineEvent(''Intelligence'', Entity  () removed.);
      break;
    }

    case ''NOTE_ADDED'': {
      qc.setQueryData(['workspace', 'notes', case_id], (old: any) => {
        if (!old) return [{ markdown: payload.markdown, id: ''optimistic'', created_at: timestamp }];
        // If note exists, update it, otherwise create new
        if (old.length > 0) {
            const updated = [...old];
            updated[0] = { ...updated[0], markdown: payload.markdown };
            return updated;
        }
        return [{ markdown: payload.markdown, id: ''optimistic'', created_at: timestamp }];
      });
      break;
    }

    case ''CASE_UPDATED'': {
      qc.setQueryData(['workspace', 'meta', case_id], (old: any) => {
        if (!old) return old;
        return { ...old, ...payload };
      });
      addTimelineEvent(''Investigation'', ''Case details updated.'');
      break;
    }
  }
};
