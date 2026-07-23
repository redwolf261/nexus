# NEXUS Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.0-rc1] — 2026-07-23

### 🚀 Initial Release Candidate

This release marks the first production-ready candidate of the NEXUS Tactical Intelligence & Operational Command Platform. It represents the culmination of Phases 1–9 of development, covering the full analytical, operational, governance, and compliance subsystems.

---

### Added

#### Core Intelligence (Phases 1–7)
- **Synthetic Digital Twin Generator**: Hyper-realistic Karnataka State Police synthetic dataset (FIRs, persons, vehicles, criminals, gangs, patrol routes, CDRs, CCTV, financial transactions) with configurable scale (small/medium/large/research).
- **Silo Buster Engine**: Neo4j Cypher-based cross-jurisdictional graph traversal with PageRank mastermind scoring, community detection, and campaign timeline reconstruction.
- **Entity Resolution Engine**: Jaro-Winkler + phonetic deduplication across FIRs, persons, and vehicle records.
- **DBSCAN Crime Series Clustering**: Spatial-temporal clustering of related crime incidents.
- **CUSUM Anomaly Detection**: Temporal spike detection on crime rate timeseries.
- **XAI Evidence Chains**: Every analytical connection cites explicit, readable evidence — no black-box decisions.
- **Tactical GIS Intelligence Map**: Animated patrol deployment, district boundary heatmaps, and time-machine crime campaign replay.

#### Operational Command Engine (Phase 8.1–8.3)
- **Task DAG Engine**: Dependency-aware task execution engine with topological ordering, cycle detection, and SLA state machine (CREATED → IN_PROGRESS → COMPLETED/BLOCKED).
- **Workload & Assignment Engine**: Multi-factor capability scoring, Gini coefficient workload balance measurement, jurisdiction enforcement, and override rationale capture.
- **Supervisor Command Center**: Live officer workload dashboard, district health monitoring, and active investigation tracking.
- **Executive Analytics Dashboard**: District performance KPIs, crime trend analysis, officer utilization heatmaps, and exportable reports.
- **Investigation Workspace**: Collaborative evidence management, entity linking, activity timeline, and note-taking.

#### Governance & Communication (Phase 8.4–8.5)
- **Multi-Tier Approval Workflow**: Policy-validated approval chains supporting SUPERVISOR → ACP → DCP → COMMISSIONER routing, auto-delegation with expiry timers, and cascading escalation.
- **Automated Escalation Engine**: SLA breach detection, supervisor delegation, resolution tracking, and audit-integrated status updates.
- **Priority Notification Hub**: 8 deterministic digest types (DAILY, SHIFT, URGENT, WEEKLY, SLA, ESCALATION, APPROVAL, COMPLIANCE), escalating reminder sequences, entity-threaded inbox, and channel-aware routing.

#### Audit & Compliance (Phase 8.6)
- **Immutable Audit Ledger**: SHA-256 hash-chained append-only ledger with correlation ID / request ID / session ID tracking, actor attribution, IP metadata, entity version capture, previous/new value snapshots, and O(N) cryptographic integrity verification.
- **Compliance Monitoring Engine**: 20 deterministic policy rules covering authorization, assignment, approval, escalation, notification, audit, evidence, and authentication domains. Subsystem risk scoring (0–100) with risk band classification (LOW / MODERATE / HIGH / CRITICAL) and continuous background scanner.
- **Compliance REST API**: `/api/compliance` endpoints for dashboard, violations, entity/user lookups, rules catalog, background scan triggers, risk recalculation, historical trends, and RBAC-protected exports.

#### Frontend (Phase 9.0)
- **Typed API Client** (`frontend/services/apiClient.ts`): Centralized JWT-authenticated gateway with retry logic connecting all React panels to FastAPI endpoints.
- **Operational React Hooks** (`frontend/hooks/useApi.ts`): TanStack Query hooks for Audit Ledger, Compliance Dashboard, Approval Queue, Escalation Queue, and Notification Inbox.
- **Compliance UI Suite**: `ComplianceDashboard`, `ViolationsTable`, `RiskGauge`, `RuleViewer`, `ComplianceTimeline`, `RemediationPanel`, `ScanStatus`, `ComplianceFilters`.
- **Audit UI Suite**: `AuditTimeline`, `EntityHistoryViewer`, `IntegrityStatusWidget`, `UserActivityViewer`, `CorrelationExplorer`, `AuditSearchPanel`.

#### Infrastructure (Phase 9.1)
- **Docker Compose**: Full stack deployment (PostgreSQL, Neo4j, FastAPI backend, Next.js frontend) with health checks and auto-seeding.
- **Backend Dockerfile** (`backend/Dockerfile`): Python 3.11 slim image with `libpq-dev` for PostgreSQL.
- **Frontend Dockerfile** (`frontend/Dockerfile`): Multi-stage Node 20 build with Next.js standalone output.
- **Demo Data Seeder** (`backend/seed_demo.py`): One-command Karnataka Police synthetic dataset seeder covering 5 district command stations, 25 officers, 5 investigations, 5 DAG tasks, SHA-256 audit chain, and compliance violations.
- **Comprehensive README**: Reviewer-ready documentation with architecture diagram, quick start, demo credentials, API overview, performance table, and testing summary.

#### Testing
- **1,070 automated test cases** across all subsystems with 0 failures.
- **E2E Workflow Tests** (`test_e2e_workflows.py`): Investigation Lifecycle, Approval Lifecycle, and Escalation Lifecycle end-to-end workflows.

---

### Performance (All SLA targets met)

| Operation | SLA | Result |
|:---|:---|:---|
| Workspace Loading | < 50 ms | 14.2 ms |
| Task DAG Resolution | < 10 ms | 2.1 ms |
| Assignment Recommendation | < 15 ms | 4.8 ms |
| Approval Queue Query | < 10 ms | 3.1 ms |
| Audit Hash Chaining | < 10 ms | 1.2 ms |
| Cryptographic Chain Sweep (500) | < 50 ms | 12.5 ms |
| Compliance Rule Evaluation | < 10 ms | 0.9 ms |
| Compliance Dashboard | < 75 ms | 18.6 ms |

---

### Known Limitations

- **Neo4j Dependency**: The Silo Buster graph intelligence requires a running Neo4j 5.x instance. Features degrade gracefully to relational-only mode if Neo4j is unavailable.
- **PostgreSQL Full-Text Indexes**: `pg_trgm` extension and GIN indexes are created on first startup; SQLite test runner uses in-memory tables without these indexes.
- **Demo Credentials**: Hardcoded demo passwords (`nexus2026`) are for evaluation only. Production deployments must use environment-variable-managed secrets.
- **Simulator Runtime**: Generating a `large`-scale synthetic dataset takes 3–8 minutes depending on hardware.

---

### Future Roadmap

- **v1.1**: Live CCTNS ETL pipeline replacing the synthetic data simulator
- **v1.2**: Mobile command app (React Native) for field officers  
- **v2.0**: Federated multi-district deployment with cross-district secure intelligence sharing
- **v2.1**: Predictive patrol deployment model using historical crime pattern analysis

---

*NEXUS v1.0.0-rc1 — Karnataka State Police Datathon 2026*
