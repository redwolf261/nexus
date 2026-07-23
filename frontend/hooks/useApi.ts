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

// ── Existing Hooks ─────────────────────────────────────────────────────────

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

export function useInvestigations() {
  return useQuery({
    queryKey: ["investigations"],
    queryFn: getInvestigations,
    staleTime: 15_000,
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
