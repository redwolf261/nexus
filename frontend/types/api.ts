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

export interface ExecutiveDashboardResponse {
  todays_firs: number;
  active_campaigns: number;
  predicted_hotspots: number;
  average_investigation_time: number;
  crime_trend: string;
  new_intelligence_alerts: number;
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

export interface CampaignSummaryResponse {
  campaign_id: string;
  mastermind: string;
  gang: string;
  vehicles: string[];
  phones: string[];
  timeline_events: number;
  status: string;
}

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
