from pydantic import BaseModel, Field
from typing import List, Optional, Any

class LinkedEntity(BaseModel):
    linked_fir: str
    shared_type: List[str]
    entity_id: str

class CrossJurisdictionResponse(BaseModel):
    fir_id: str
    score: int
    confidence: float
    reasons: List[str] = Field(description="Explainable reasons why these crimes are linked")
    linked_crimes: List[LinkedEntity]

class CampaignResponse(BaseModel):
    mastermind: str
    gang: str
    campaign_count: int

class HotspotResponse(BaseModel):
    cluster_id: str
    lat: float
    lng: float
    intensity: float

class TimelineEvent(BaseModel):
    day: int
    event_type: str
    entity_id: str
    description: str

class CampaignTimelineResponse(BaseModel):
    campaign_id: str
    events: List[TimelineEvent]

class GraphNeighbor(BaseModel):
    node_id: str
    labels: List[str]
    relationship: str

class GraphPersonResponse(BaseModel):
    person_id: str
    risk_score: int
    centrality: float
    campaigns: List[str]
    reasons: List[str] = Field(description="Explainable reasons for this risk score")
    neighbors: List[GraphNeighbor]

class OfficerDashboardResponse(BaseModel):
    officer_id: str
    cases_open: int
    cases_closed: int
    average_delay_days: float
    workload: str
    patrol_area: str

class ExecutiveDashboardResponse(BaseModel):
    todays_firs: int
    active_campaigns: int
    predicted_hotspots: int
    average_investigation_time: float
    crime_trend: str
    new_intelligence_alerts: int

class DistrictDashboardResponse(BaseModel):
    district_id: str
    top_gangs: List[str]
    repeat_offenders: int
    risk_score: int
    patrol_coverage: str
    crime_trend: str

class CampaignSummaryResponse(BaseModel):
    campaign_id: str
    mastermind: str
    gang: str
    vehicles: List[str]
    phones: List[str]
    timeline_events: int
    status: str

class SearchResult(BaseModel):
    type: str
    id: str
    name: str
    snippet: str

class OmniSearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
