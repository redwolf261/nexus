"use client";

import { useQuery } from "@tanstack/react-query";
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
} from "@/lib/api";
import type { FIRFilters } from "@/types/api";

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
