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
  headers: { 
    "Content-Type": "application/json"
  },
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? (localStorage.getItem("nexus_token") || localStorage.getItem("dev_token")) : null;
  const envToken = process.env.NEXT_PUBLIC_DEV_AUTH_TOKEN;
  const finalToken = token || envToken;
  if (finalToken) {
    config.headers.Authorization = `Bearer ${finalToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("nexus_token");
      localStorage.removeItem("dev_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

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

// ── Investigations ─────────────────────────────────────────────────────────
export async function getInvestigations(status?: string) {
  let url = '/api/investigations';
  if (status) url += `?status=${status}`;
  const res = await api.get(url);
  return res.data;
}

export async function createInvestigation(data: { title: string, description?: string, priority: string }) {
  const res = await api.post('/api/investigations', data);
  return res.data;
}

export async function getInvestigationWorkspace(id: string) {
  const res = await api.get(`/api/investigations/${id}/workspace`);
  return res.data;
}

export async function addEntityToInvestigation(invId: string, entityType: string, entityId: string) {
  const res = await api.post(`/api/investigations/${invId}/entities?entity_type=${entityType}&entity_id=${entityId}`);
  return res.data;
}

export async function removeEntityFromInvestigation(invId: string, entityType: string, entityId: string) {
  const res = await api.delete(`/api/investigations/${invId}/entities/${entityId}?entity_type=${entityType}`);
  return res.data;
}

export async function addInvestigationNote(invId: string, markdown: string) {
  const res = await api.post(`/api/investigations/${invId}/notes`, { markdown });
  return res.data;
}

export async function updateInvestigation(invId: string, data: { status?: string, priority?: string, title?: string }) {
  const res = await api.patch(`/api/investigations/${invId}`, data);
  return res.data;
}
