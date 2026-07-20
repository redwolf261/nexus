import axios from "axios";
import type {
  ExecutiveDashboardResponse,
  DistrictDashboardResponse,
  FIRResponse,
  FIRDetailResponse,
  PersonDetailResponse,
  VehicleDetailResponse,
  CriminalDetailResponse,
  HotspotResponse,
  CrossJurisdictionResponse,
  GraphPersonResponse,
  CampaignTimelineResponse,
  CampaignSummaryResponse,
  OmniSearchResponse,
  FIRFilters,
} from "@/types/api";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Legacy export alias so existing imports of `api` keep working
export const api = apiClient;

// ── Dashboard ──────────────────────────────────────────────────────────────

export const getExecutiveDashboard = (): Promise<ExecutiveDashboardResponse> =>
  apiClient.get("/api/dashboard/executive").then((r) => r.data);

export const getDistrictDashboard = (districtId: string): Promise<DistrictDashboardResponse> =>
  apiClient.get(`/api/district/${districtId}`).then((r) => r.data);

// ── FIRs ──────────────────────────────────────────────────────────────────

export const getFIRs = (filters: FIRFilters = {}): Promise<FIRResponse[]> =>
  apiClient.get("/api/firs", { params: filters }).then((r) => r.data);

export const getFIRDetail = (firId: string): Promise<FIRDetailResponse> =>
  apiClient.get(`/api/fir/${firId}`).then((r) => r.data);

// ── Entity Detail ──────────────────────────────────────────────────────────

export const getPersonDetail = (personId: string): Promise<PersonDetailResponse> =>
  apiClient.get(`/api/person/${personId}`).then((r) => r.data);

export const getVehicleDetail = (vehicleId: string): Promise<VehicleDetailResponse> =>
  apiClient.get(`/api/vehicle/${vehicleId}`).then((r) => r.data);

export const getCriminalDetail = (criminalId: string): Promise<CriminalDetailResponse> =>
  apiClient.get(`/api/criminal/${criminalId}`).then((r) => r.data);

// ── Analytics ─────────────────────────────────────────────────────────────

export const getHotspots = (): Promise<HotspotResponse[]> =>
  apiClient.get("/api/analytics/hotspots").then((r) => r.data);

export const getSiloBuster = (firId: string): Promise<CrossJurisdictionResponse> =>
  apiClient
    .get("/api/analytics/cross-jurisdiction", { params: { fir_id: firId } })
    .then((r) => r.data);

export const getPersonGraph = (personId: string): Promise<GraphPersonResponse> =>
  apiClient.get(`/api/graph/person/${personId}`).then((r) => r.data);

export const getCampaignTimeline = (campaignId: string): Promise<CampaignTimelineResponse> =>
  apiClient.get(`/api/timeline/${campaignId}`).then((r) => r.data);

export const getCampaignSummary = (campaignId: string): Promise<CampaignSummaryResponse> =>
  apiClient.get(`/api/campaign/${campaignId}/summary`).then((r) => r.data);

// ── Search ─────────────────────────────────────────────────────────────────

export const search = (query: string): Promise<OmniSearchResponse> =>
  apiClient.get("/api/search", { params: { q: query } }).then((r) => r.data);
