from fastapi import APIRouter
from typing import List

from backend.schemas.analytics import (
    CrossJurisdictionResponse,
    CampaignResponse,
    HotspotResponse,
    CampaignTimelineResponse,
    ExecutiveDashboardResponse,
    DistrictDashboardResponse,
    CampaignSummaryResponse
)
from backend.services.analytics_service import (
    get_cross_jurisdiction_service,
    get_campaigns_service,
    get_hotspots_service,
    get_campaign_timeline_service,
    get_executive_dashboard_service,
    get_district_dashboard_service,
    get_campaign_summary_service
)

router = APIRouter(prefix="/api", tags=["Analytics"])

@router.get("/dashboard/executive", response_model=ExecutiveDashboardResponse)
def get_executive_dashboard():
    """Returns top-level KPIs for the landing page."""
    return get_executive_dashboard_service()

@router.get("/district/{district_id}", response_model=DistrictDashboardResponse)
def get_district_dashboard(district_id: str):
    """Returns analytics specific to a police district."""
    return get_district_dashboard_service(district_id)

@router.get("/analytics/cross-jurisdiction", response_model=CrossJurisdictionResponse)
def get_cross_jurisdiction(fir_id: str):
    """Finds isolated FIRs linked through shared entities (Silo Buster)."""
    return get_cross_jurisdiction_service(fir_id)

@router.get("/analytics/community-detection", response_model=List[CampaignResponse])
def get_community_detection():
    """Returns detected criminal campaigns and masterminds."""
    return get_campaigns_service()

@router.get("/analytics/hotspots", response_model=List[HotspotResponse])
def get_hotspots():
    """Returns pre-calculated high-risk geospatial clusters."""
    return get_hotspots_service()

@router.get("/campaign/{campaign_id}/summary", response_model=CampaignSummaryResponse)
def get_campaign_summary(campaign_id: str):
    """Returns a unified payload for a campaign including mastermind, gang, and assets."""
    return get_campaign_summary_service(campaign_id)

@router.get("/timeline/{campaign_id}", response_model=CampaignTimelineResponse)
def get_campaign_timeline(campaign_id: str):
    """Replays the temporal sequence of a criminal campaign."""
    return get_campaign_timeline_service(campaign_id)
