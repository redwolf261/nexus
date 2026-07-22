"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  getExecutiveDashboard,
  getDistrictDashboard,
  getFIRs,
  getFIRDetail,
  getPersonDetail,
  getVehicleDetail,
  getCriminalDetail,
  getHotspots,
  getSiloBuster,
  getPersonGraph,
  getCampaignTimeline,
  getCampaignSummary,
  search,
  getInvestigations,
  createInvestigation,
  updateInvestigation,
  addEntityToInvestigation,
  removeEntityFromInvestigation,
  addInvestigationNote
} from "@/lib/api";
import type { FIRFilters } from "@/types/api";
import { api } from "@/lib/api";
import { applyEventReducer } from "@/lib/eventReducers";

// ── Dashboard ──────────────────────────────────────────────────────────────

export function useExecutiveDashboard() {
  return useQuery({
    queryKey: ["executiveDashboard"],
    queryFn: getExecutiveDashboard,
    staleTime: 30_000,
    retry: 2,
  });
}

export function useDistrictDashboard(districtId: string) {
  return useQuery({
    queryKey: ["districtDashboard", districtId],
    queryFn: () => getDistrictDashboard(districtId),
    enabled: !!districtId,
    staleTime: 30_000,
    retry: 2,
  });
}

// ── FIRs ──────────────────────────────────────────────────────────────────

export function useFIRs(filters: FIRFilters = {}) {
  return useQuery({
    queryKey: ["firs", filters],
    queryFn: () => getFIRs(filters),
    staleTime: 30_000,
    retry: 2,
  });
}

export function useFIRDetail(firId: string | null) {
  return useQuery({
    queryKey: ["firDetail", firId],
    queryFn: () => getFIRDetail(firId!),
    enabled: !!firId,
    staleTime: 60_000,
    retry: 2,
  });
}

// ── Entity Detail ──────────────────────────────────────────────────────────

export function usePersonDetail(personId: string | null) {
  return useQuery({
    queryKey: ["personDetail", personId],
    queryFn: () => getPersonDetail(personId!),
    enabled: !!personId,
    staleTime: 60_000,
    retry: 2,
  });
}

export function useVehicleDetail(vehicleId: string | null) {
  return useQuery({
    queryKey: ["vehicleDetail", vehicleId],
    queryFn: () => getVehicleDetail(vehicleId!),
    enabled: !!vehicleId,
    staleTime: 60_000,
    retry: 2,
  });
}

export function useCriminalDetail(criminalId: string | null) {
  return useQuery({
    queryKey: ["criminalDetail", criminalId],
    queryFn: () => getCriminalDetail(criminalId!),
    enabled: !!criminalId,
    staleTime: 60_000,
    retry: 2,
  });
}

// ── Analytics ─────────────────────────────────────────────────────────────

export function useHotspots() {
  return useQuery({
    queryKey: ["hotspots"],
    queryFn: getHotspots,
    staleTime: 120_000,
    retry: 2,
  });
}

export function useSiloBuster(firId: string) {
  return useQuery({
    queryKey: ["siloBuster", firId],
    queryFn: () => getSiloBuster(firId),
    enabled: !!firId,
    staleTime: 60_000,
    retry: 2,
  });
}

export function usePersonGraph(personId: string | null) {
  return useQuery({
    queryKey: ["personGraph", personId],
    queryFn: () => getPersonGraph(personId!),
    enabled: !!personId,
    staleTime: 60_000,
    retry: 2,
  });
}

export function useCampaignTimeline(campaignId: string | null) {
  return useQuery({
    queryKey: ["campaignTimeline", campaignId],
    queryFn: () => getCampaignTimeline(campaignId!),
    enabled: !!campaignId,
    staleTime: 60_000,
    retry: 2,
  });
}

export function useCampaignSummary(campaignId: string | null) {
  return useQuery({
    queryKey: ["campaignSummary", campaignId],
    queryFn: () => getCampaignSummary(campaignId!),
    enabled: !!campaignId,
    staleTime: 60_000,
    retry: 2,
  });
}

// ── Search (debounced) ─────────────────────────────────────────────────────

export function useSearch(query: string) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: () => search(query),
    enabled: query.trim().length >= 2,
    staleTime: 15_000,
    retry: 1,
  });
}

// ── Investigations ─────────────────────────────────────────────────────────

export function useInvestigations(status?: string) {
  return useQuery({
    queryKey: ["investigations", status],
    queryFn: () => getInvestigations(status),
    staleTime: 10_000,
  });
}

export function useInvestigationMutations() {
  const qc = useQueryClient();

  const create = useMutation({ mutationFn: createInvestigation, onSuccess: () => qc.invalidateQueries({ queryKey: ["investigations"] }) });
  
  const update = useMutation({ 
    mutationFn: ({id, data}: {id: string, data: any}) => updateInvestigation(id, data), 
    onSuccess: () => qc.invalidateQueries({ queryKey: ["investigations"] }) 
  });
  
  const addEntity = useMutation({ 
    mutationFn: ({invId, type, id}: {invId: string, type: string, id: string}) => addEntityToInvestigation(invId, type, id), 
    onMutate: async ({invId, type, id}) => {
      await qc.cancelQueries({ queryKey: ["workspace", "entities", invId] });
      await qc.cancelQueries({ queryKey: ["workspace", "timeline", invId] });
      const prevEntities = qc.getQueryData(["workspace", "entities", invId]);
      const prevTimeline = qc.getQueryData(["workspace", "timeline", invId]);
      
      applyEventReducer(qc, {
          case_id: invId,
          event_type: "ENTITY_ATTACHED",
          payload: { entity_type: type, entity_id: id }
      });
      
      return { prevEntities, prevTimeline, invId };
    },
    onError: (err, variables, context: any) => {
      if (context?.prevEntities) qc.setQueryData(["workspace", "entities", context.invId], context.prevEntities);
      if (context?.prevTimeline) qc.setQueryData(["workspace", "timeline", context.invId], context.prevTimeline);
    }
  });
  
  const removeEntity = useMutation({ 
    mutationFn: ({invId, type, id}: {invId: string, type: string, id: string}) => removeEntityFromInvestigation(invId, type, id),
    onMutate: async ({invId, type, id}) => {
      await qc.cancelQueries({ queryKey: ["workspace", "entities", invId] });
      await qc.cancelQueries({ queryKey: ["workspace", "timeline", invId] });
      const prevEntities = qc.getQueryData(["workspace", "entities", invId]);
      const prevTimeline = qc.getQueryData(["workspace", "timeline", invId]);
      
      applyEventReducer(qc, {
          case_id: invId,
          event_type: "ENTITY_REMOVED",
          payload: { entity_type: type, entity_id: id }
      });
      
      return { prevEntities, prevTimeline, invId };
    },
    onError: (err, variables, context: any) => {
      if (context?.prevEntities) qc.setQueryData(["workspace", "entities", context.invId], context.prevEntities);
      if (context?.prevTimeline) qc.setQueryData(["workspace", "timeline", context.invId], context.prevTimeline);
    }
  });
  
  const addNote = useMutation({ 
    mutationFn: ({invId, markdown}: {invId: string, markdown: string}) => addInvestigationNote(invId, markdown),
    onMutate: async ({invId, markdown}) => {
      await qc.cancelQueries({ queryKey: ["workspace", "notes", invId] });
      const prevNotes = qc.getQueryData(["workspace", "notes", invId]);
      
      applyEventReducer(qc, {
          case_id: invId,
          event_type: "NOTE_ADDED",
          payload: { markdown }
      });
      
      return { prevNotes, invId };
    },
    onError: (err, variables, context: any) => {
      if (context?.prevNotes) qc.setQueryData(["workspace", "notes", context.invId], context.prevNotes);
    }
  });

  return { create, update, addEntity, removeEntity, addNote };
}

// ── Intelligence ─────────────────────────────────────────────────────────

export function useEntityIntelligence(entityId: string, entityType: string) {
  return useQuery({
    queryKey: ["intelligence", entityId, entityType],
    queryFn: async () => { const res = await api.get(`/api/intelligence/entity/?entity_type=${entityType}&entity_id=${entityId}`); return res.data; },
    staleTime: 60000,
  });
}

export function useCaseRecommendations(caseId: string) {
  return useQuery({
    queryKey: ["recommendations", caseId],
    queryFn: async () => { const res = await api.get(`/api/intelligence/recommendations/`); return res.data; },
    staleTime: 60000,
  });
}

export function useEntityLinks(entityId: string, entityType: string) {
  return useQuery({
    queryKey: ["links", entityId, entityType],
    queryFn: async () => { const res = await api.get(`/api/intelligence/links/?entity_type=${entityType}&entity_id=${entityId}`); return res.data; },
    staleTime: 60000,
  });
}

export function useCaseRisk(caseId: string) {
  return useQuery({
    queryKey: ["caseRisk", caseId],
    queryFn: async () => { const res = await api.get(`/api/intelligence/risk/`); return res.data; },
    staleTime: 60000,
  });
}

export function useCaseOverlaps(caseId: string) {
  return useQuery({
    queryKey: ["overlaps", caseId],
    queryFn: async () => { const res = await api.get(`/api/intelligence/overlaps/`); return res.data; },
    staleTime: 60000,
  });
}
