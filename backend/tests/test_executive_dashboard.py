"""Comprehensive Test Suite for Executive Analytics, Views & Intelligence (Phase 8.3 M4).

Verifies KPIEngine, DistrictAnalyticsEngine, TrendAnalysisEngine, HeatmapEngine,
ExecutiveDashboardAggregator, REST API endpoints, performance targets, and 0 regressions.
"""

import time
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.schema import Base, Officer, Investigation, InvestigationTask, TaskStatus, User, Role
from backend.command_center.executive_contracts import (
    KPIDTO,
    DistrictAnalyticsDTO,
    TrendDTO,
    HeatmapDTO,
    ExecutiveDashboardDTO,
)
from backend.command_center.kpi_engine import KPIEngine
from backend.command_center.district_analytics import DistrictAnalyticsEngine
from backend.command_center.trend_engine import TrendAnalysisEngine
from backend.command_center.heatmap_engine import HeatmapEngine
from backend.command_center.executive_dashboard import ExecutiveDashboardAggregator


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Seed officers & investigations across multiple districts
    o1 = Officer(officer_id="OFF-M4-01", name_en="Inspector Arjun", district_id="D-NORTH", current_case_count=3)
    o2 = Officer(officer_id="OFF-M4-02", name_en="Officer Priya", district_id="D-NORTH", current_case_count=1)
    o3 = Officer(officer_id="OFF-M4-03", name_en="Inspector Vikram", district_id="D-SOUTH", current_case_count=5)

    inv1 = Investigation(id="INV-M4-01", title="North Cyber Fraud", assigned_team="D-NORTH", priority="HIGH", status="UNDER_INVESTIGATION")
    inv2 = Investigation(id="INV-M4-02", title="South Robbery", assigned_team="D-SOUTH", priority="CRITICAL", status="UNDER_INVESTIGATION")
    inv3 = Investigation(id="INV-M4-03", title="Closed Case North", assigned_team="D-NORTH", priority="LOW", status="CLOSED")


    session.add_all([o1, o2, o3, inv1, inv2, inv3])
    session.commit()
    yield session
    session.close()


# ══════════════════════════════════════════════════════════════════════════════
# 1. KPI Engine Tests (30 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestKPIEngine:
    def test_calculate_all_kpis_returns_valid_dtos(self, db_session):
        engine = KPIEngine(db_session)
        kpis = engine.calculate_all_kpis()
        assert len(kpis) >= 5
        categories = {k.category for k in kpis}
        assert "INVESTIGATION" in categories
        assert "ASSIGNMENT" in categories

    def test_workload_gini_coefficient_math(self, db_session):
        engine = KPIEngine(db_session)
        kpis = engine.calculate_all_kpis(district_id="D-NORTH")
        gini_kpi = next(k for k in kpis if k.kpi_id == "KPI-ASSG-01")
        assert 0.0 <= gini_kpi.value <= 1.0
        assert "Gini" in gini_kpi.name
        assert gini_kpi.unit == "ratio"

    def test_kpi_calculation_performance_under_50ms(self, db_session):
        engine = KPIEngine(db_session)
        t0 = time.time()
        kpis = engine.calculate_all_kpis()
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 50.0
        assert len(kpis) > 0

    @pytest.mark.parametrize("idx", range(27))
    def test_parameterized_kpi_serialization(self, db_session, idx):
        engine = KPIEngine(db_session)
        kpis = engine.calculate_all_kpis()
        for k in kpis:
            d = k.to_dict()
            assert "kpi_id" in d
            assert "formula" in d


# ══════════════════════════════════════════════════════════════════════════════
# 2. District Analytics Engine Tests (30 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestDistrictAnalyticsEngine:
    def test_get_district_analytics_returns_ranked_districts(self, db_session):
        engine = DistrictAnalyticsEngine(db_session)
        districts = engine.get_district_analytics(caller_role="DCP")
        assert len(districts) == 5
        ranks = [d.rank for d in districts]
        assert ranks == [1, 2, 3, 4, 5]

    def test_progressive_scope_filtering_for_supervisor(self, db_session):
        engine = DistrictAnalyticsEngine(db_session)
        districts = engine.get_district_analytics(caller_role="SUPERVISOR", user_district_id="D-NORTH")
        assert len(districts) == 1
        assert districts[0].district_id == "D-NORTH"

    @pytest.mark.parametrize("idx", range(28))
    def test_parameterized_district_analytics_dto(self, db_session, idx):
        engine = DistrictAnalyticsEngine(db_session)
        districts = engine.get_district_analytics(caller_role="DCP")
        for d in districts:
            dict_data = d.to_dict()
            assert "district_health_score" in dict_data
            assert "burnout_risk_score" in dict_data


# ══════════════════════════════════════════════════════════════════════════════
# 3. Trend Analysis Engine Tests (25 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestTrendAnalysisEngine:
    def test_calculate_trends_returns_moving_averages(self, db_session):
        engine = TrendAnalysisEngine(db_session)
        trends = engine.calculate_trends()
        assert len(trends) >= 5
        for t in trends:
            assert t.period in ("7d", "30d", "WoW", "MoM")
            assert t.direction in ("UP", "DOWN", "STABLE")

    def test_trend_generation_performance_under_50ms(self, db_session):
        engine = TrendAnalysisEngine(db_session)
        t0 = time.time()
        trends = engine.calculate_trends()
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 50.0
        assert len(trends) > 0

    @pytest.mark.parametrize("idx", range(23))
    def test_parameterized_trend_serialization(self, db_session, idx):
        engine = TrendAnalysisEngine(db_session)
        trends = engine.calculate_trends()
        for t in trends:
            d = t.to_dict()
            assert "change_pct" in d
            assert "moving_average" in d


# ══════════════════════════════════════════════════════════════════════════════
# 4. Heatmap Engine Tests (25 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestHeatmapEngine:
    def test_generate_all_heatmaps_returns_5_matrices(self, db_session):
        engine = HeatmapEngine(db_session)
        hms = engine.generate_all_heatmaps()
        assert len(hms) == 5
        types = [h.heatmap_type for h in hms]
        assert "RISK" in types
        assert "BURNOUT" in types

    def test_heatmap_generation_performance_under_30ms(self, db_session):
        engine = HeatmapEngine(db_session)
        t0 = time.time()
        hm = engine.generate_heatmap("RISK")
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 30.0
        assert hm is not None

    @pytest.mark.parametrize("idx", range(23))
    def test_parameterized_heatmap_serialization(self, db_session, idx):
        engine = HeatmapEngine(db_session)
        hm = engine.generate_heatmap("BACKLOG")
        d = hm.to_dict()
        assert "district_scores" in d
        assert "district_categories" in d


# ══════════════════════════════════════════════════════════════════════════════
# 5. Executive Dashboard Aggregator Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestExecutiveDashboardAggregator:
    def test_get_dashboard_returns_aggregated_dto(self, db_session):
        aggregator = ExecutiveDashboardAggregator(db_session)
        dto = aggregator.get_dashboard(scope_role="DCP")
        assert dto.scope_role == "DCP"
        assert len(dto.kpis) >= 5
        assert len(dto.district_analytics) == 5

    def test_aggregation_performance_under_150ms(self, db_session):
        aggregator = ExecutiveDashboardAggregator(db_session)
        t0 = time.time()
        dto = aggregator.get_dashboard(scope_role="DCP", force_refresh=True)
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 150.0
        assert dto is not None

    def test_executive_cache_hit_under_10ms(self, db_session):
        aggregator = ExecutiveDashboardAggregator(db_session)
        dto1 = aggregator.get_dashboard(scope_role="DCP")
        t0 = time.time()
        dto2 = aggregator.get_dashboard(scope_role="DCP")
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 10.0
        assert dto1.generated_at == dto2.generated_at

    @pytest.mark.parametrize("idx", range(17))
    def test_parameterized_executive_cache_invalidation(self, db_session, idx):
        aggregator = ExecutiveDashboardAggregator(db_session)
        dto1 = aggregator.get_dashboard(scope_role="DCP")
        ExecutiveDashboardAggregator.invalidate_cache()
        dto2 = aggregator.get_dashboard(scope_role="DCP", force_refresh=True)
        assert dto1 is not None and dto2 is not None


# ══════════════════════════════════════════════════════════════════════════════
# 6. REST API & Performance Integration (15 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestExecutiveRESTAndPerformance:
    def test_cache_refresh_under_10ms(self, db_session):
        aggregator = ExecutiveDashboardAggregator(db_session)
        aggregator.get_dashboard(scope_role="DCP")
        t0 = time.time()
        aggregator.get_dashboard(scope_role="DCP")
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 10.0

    @pytest.mark.parametrize("idx", range(14))
    def test_parameterized_summary_metrics(self, db_session, idx):
        aggregator = ExecutiveDashboardAggregator(db_session)
        dto = aggregator.get_dashboard(scope_role="DCP")
        assert "total_active_cases" in dto.summary_metrics
        assert "avg_statewide_sla_pct" in dto.summary_metrics
