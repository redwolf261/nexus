// ── Shared primitives ──────────────────────────────────────────────────────

export interface FIRResponse {
  fir_id: string;
  fir_number?: string;
  station_id?: string;
  district_id?: string;
  district_name?: string;
  occurred_date?: string;
  crime_type?: string;
  crime_category?: string;
  severity?: number;
  status?: string;
  description_en?: string;
  latitude?: number;
  longitude?: number;
  is_gang_crime?: boolean;
  campaign_id?: string;
  estimated_loss_inr?: number;
}

// ── Investigation Drawer detail types ─────────────────────────────────────

export interface AccusedSummary {
  accused_id: string;
  name_en?: string;
  age?: number;
  gender?: string;
  role?: string;
  is_arrested?: boolean;
}

export interface VictimSummary {
  victim_id: string;
  name_en?: string;
  age?: number;
  gender?: string;
  injury_type?: string;
}

export interface InvLogEntry {
  log_id: string;
  event_type?: string;
  timestamp?: string;
  description?: string;
  location?: string;
}

export interface VehicleSummary {
  vehicle_id: string;
  license_plate?: string;
  make?: string;
  model?: string;
  color?: string;
  is_stolen?: boolean;
}

export interface PhoneSummary {
  phone_id: string;
  phone_number?: string;
  provider?: string;
  is_burner?: boolean;
}

export interface CriminalSummary {
  criminal_id: string;
  name_en?: string;
  risk_level?: string;
  expertise?: string;
  total_crimes_committed?: number;
  is_currently_active?: boolean;
  gang_id?: string;
}

export interface GangSummary {
  gang_id: string;
  name?: string;
  specialization?: string;
  threat_level?: string;
  num_members?: number;
}

export interface ArrestSummary {
  arrest_id: string;
  arrest_date?: string;
  arrest_location?: string;
  bail_granted?: boolean;
  is_convicted?: boolean;
}

export interface FIRDetailResponse {
  fir: FIRResponse;
  accused: AccusedSummary[];
  victims: VictimSummary[];
  evidence_count: number;
  investigation_logs: InvLogEntry[];
  linked_vehicles: VehicleSummary[];
  linked_phones: PhoneSummary[];
}

export interface PersonResponse {
  citizen_id: string;
  name_en?: string;
  gender?: string;
  age?: number;
  phone_primary?: string;
  occupation?: string;
  district_name?: string;
  is_migrant?: boolean;
}

export interface PersonDetailResponse {
  person: PersonResponse;
  criminal?: CriminalSummary;
  linked_firs: FIRResponse[];
  vehicles: VehicleSummary[];
  phones: PhoneSummary[];
  gang?: GangSummary;
}

export interface VehicleDetailResponse {
  vehicle: VehicleSummary;
  owner?: PersonResponse;
  linked_firs: FIRResponse[];
}

export interface CriminalDetailResponse {
  criminal: CriminalSummary;
  gang?: GangSummary;
  linked_firs: FIRResponse[];
  associates: CriminalSummary[];
  arrests: ArrestSummary[];
}

// ── Dashboard ──────────────────────────────────────────────────────────────

export interface ExecutiveDashboardResponse {
  todays_firs: number;
  active_campaigns: number;
  predicted_hotspots: number;
  average_investigation_time: number;
  crime_trend: string;
  new_intelligence_alerts: number;
  total_firs?: number;
}

export interface DistrictDashboardResponse {
  district_id: string;
  top_gangs: string[];
  repeat_offenders: number;
  risk_score: number;
  patrol_coverage: string;
  crime_trend: string;
  total_firs?: number;
  active_gang_count?: number;
}

// ── Hotspots ───────────────────────────────────────────────────────────────

export interface HotspotResponse {
  cluster_id: string;
  lat: number;
  lng: number;
  intensity: number;
}

// ── Graph / Silo Buster ────────────────────────────────────────────────────

export interface LinkedEntity {
  linked_fir: string;
  shared_type: string[];
  entity_id: string;
}

export interface CrossJurisdictionResponse {
  fir_id: string;
  score: number;
  confidence: number;
  reasons: string[];
  linked_crimes: LinkedEntity[];
}

export interface GraphNeighbor {
  node_id: string;
  labels: string[];
  relationship: string;
}

export interface GraphPersonResponse {
  person_id: string;
  risk_score: number;
  centrality: number;
  campaigns: string[];
  reasons: string[];
  neighbors: GraphNeighbor[];
}

// ── Timeline ───────────────────────────────────────────────────────────────

export interface TimelineEvent {
  day: number;
  event_type: string;
  entity_id: string;
  description: string;
}

export interface CampaignTimelineResponse {
  campaign_id: string;
  events: TimelineEvent[];
}

// ── Campaign ───────────────────────────────────────────────────────────────

export interface CampaignSummaryResponse {
  campaign_id: string;
  mastermind: string;
  gang: string;
  vehicles: string[];
  phones: string[];
  timeline_events: number;
  status: string;
  gang_id?: string;
  crime_category?: string;
  start_date?: string;
  end_date?: string;
  num_crimes_planned?: number;
  num_crimes_committed?: number;
}

// ── Search ─────────────────────────────────────────────────────────────────

export interface SearchResult {
  type: string;
  id: string;
  name: string;
  snippet: string;
}

export interface OmniSearchResponse {
  query: string;
  results: SearchResult[];
}

// ── FIR filter params ──────────────────────────────────────────────────────

export interface FIRFilters {
  district_id?: string;
  crime_type?: string;
  crime_category?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  is_gang_crime?: boolean;
  limit?: number;
  offset?: number;
}
