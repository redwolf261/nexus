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
  addInvestigationNote,
  api
} from "@/lib/api";
import { ApiClient } from "@/services/apiClient";
import type { FIRFilters } from "@/types/api";

// ── Existing Dashboard & FIR Hooks ─────────────────────────────────────────

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

export function useFIRs(filters: FIRFilters = {}) {
  return useQuery({
    queryKey: ["firs", filters],
    queryFn: () => getFIRs(filters),
    staleTime: 30_000,
    retry: 2,
  });
}

export function useFIRDetail(firId: string) {
  return useQuery({
    queryKey: ["firDetail", firId],
    queryFn: () => getFIRDetail(firId),
    enabled: !!firId,
  });
}

export function usePersonDetail(personId: string) {
  return useQuery({
    queryKey: ["personDetail", personId],
    queryFn: () => getPersonDetail(personId),
    enabled: !!personId,
  });
}

export function useVehicleDetail(vehicleId: string) {
  return useQuery({
    queryKey: ["vehicleDetail", vehicleId],
    queryFn: () => getVehicleDetail(vehicleId),
    enabled: !!vehicleId,
  });
}

export function useCriminalDetail(criminalId: string) {
  return useQuery({
    queryKey: ["criminalDetail", criminalId],
    queryFn: () => getCriminalDetail(criminalId),
    enabled: !!criminalId,
  });
}

export function useHotspots() {
  return useQuery({
    queryKey: ["hotspots"],
    queryFn: getHotspots,
    staleTime: 60_000,
  });
}

export function useSiloBuster(firId: string) {
  return useQuery({
    queryKey: ["siloBuster", firId],
    queryFn: () => getSiloBuster(firId),
    enabled: !!firId,
  });
}

export function usePersonGraph(personId: string) {
  return useQuery({
    queryKey: ["personGraph", personId],
    queryFn: () => getPersonGraph(personId),
    enabled: !!personId,
  });
}

export function useCampaignTimeline(campaignId: string) {
  return useQuery({
    queryKey: ["campaignTimeline", campaignId],
    queryFn: () => getCampaignTimeline(campaignId),
    enabled: !!campaignId,
  });
}

export function useCampaignSummary(campaignId: string) {
  return useQuery({
    queryKey: ["campaignSummary", campaignId],
    queryFn: () => getCampaignSummary(campaignId),
    enabled: !!campaignId,
  });
}

export function useSearch(query: string) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: () => search(query),
    enabled: !!query && query.length >= 2,
  });
}

export function useInvestigations(status?: string) {
  return useQuery({
    queryKey: ["investigations", status],
    queryFn: () => getInvestigations(status),
    staleTime: 15_000,
  });
}

export function useInvestigationMutations() {
  const queryClient = useQueryClient();

  const addEntityMutation = useMutation({
    mutationFn: ({ invId, entityType, entityId }: { invId: string; entityType: string; entityId: string }) =>
      addEntityToInvestigation(invId, entityType, entityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investigations"] });
    },
  });

  const removeEntityMutation = useMutation({
    mutationFn: ({ invId, entityType, entityId }: { invId: string; entityType: string; entityId: string }) =>
      removeEntityFromInvestigation(invId, entityType, entityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investigations"] });
    },
  });

  const createNoteMutation = useMutation({
    mutationFn: ({ invId, markdown }: { invId: string; markdown: string }) =>
      addInvestigationNote(invId, markdown),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investigations"] });
    },
  });

  const createInvestigationMutation = useMutation({
    mutationFn: (data: { title: string; description?: string; priority: string }) =>
      createInvestigation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investigations"] });
    },
  });

  return {
    create: createInvestigationMutation,
    addEntity: addEntityMutation,
    removeEntity: removeEntityMutation,
    createNote: createNoteMutation,
  };
}

export function useCaseRecommendations(caseId: string) {
  return useQuery({
    queryKey: ["caseRecommendations", caseId],
    queryFn: () => ApiClient.recommendAssignment({ case_id: caseId }),
    enabled: !!caseId,
  });
}

export function useCaseRisk(caseId: string) {
  return useQuery({
    queryKey: ["caseRisk", caseId],
    queryFn: () => ApiClient.getComplianceDashboard(),
    enabled: !!caseId,
  });
}

export function useCaseOverlaps(caseId: string) {
  return useQuery({
    queryKey: ["caseOverlaps", caseId],
    queryFn: () => getSiloBuster("FIR-RBG-2021-00003"),
    enabled: !!caseId,
  });
}

// ── Phase 8.1 - 8.6 Operational Hooks ─────────────────────────────────────

export function useAuditLedger() {
  return useQuery({
    queryKey: ["auditLedger"],
    queryFn: () => ApiClient.getAuditHistory(),
    staleTime: 10_000,
  });
}

export function useComplianceDashboard() {
  return useQuery({
    queryKey: ["complianceDashboard"],
    queryFn: () => ApiClient.getComplianceDashboard(),
    staleTime: 10_000,
  });
}

export function useApprovalQueue() {
  return useQuery({
    queryKey: ["approvalQueue"],
    queryFn: () => ApiClient.getApprovals(),
    staleTime: 10_000,
  });
}

export function useEscalationQueue() {
  return useQuery({
    queryKey: ["escalationQueue"],
    queryFn: () => ApiClient.getEscalations(),
    staleTime: 10_000,
  });
}

export function useNotificationInbox() {
  return useQuery({
    queryKey: ["notificationInbox"],
    queryFn: () => ApiClient.getNotifications(),
    staleTime: 5_000,
  });
}
