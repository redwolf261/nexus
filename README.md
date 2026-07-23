<div align="center">

# 🔷 NEXUS
### Tactical Intelligence & Operational Command Platform

**Karnataka State Police Datathon 2026**

[![Tests](https://img.shields.io/badge/tests-1%2C070%20passing-brightgreen?style=flat-square)](#testing)
[![Version](https://img.shields.io/badge/version-v1.0.0--rc1-blue?style=flat-square)](#release)
[![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103%2B-009688?style=flat-square)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square)](https://nextjs.org)

*A Palantir-grade operational intelligence platform for public safety command centers.*

</div>

---

## What is NEXUS?

**NEXUS** is a production-grade operational intelligence platform built for law enforcement command centers. It transforms fragmented police records—FIRs, evidence items, suspect linkages, patrol deployments—into a single, live tactical picture.

Where most systems are passive databases, NEXUS is an **active command engine**: it creates and routes tasks, enforces governance workflows, automatically escalates SLA breaches, dispatches intelligent notifications, maintains a cryptographically immutable audit ledger, and continuously monitors policy compliance—all in real time.

> *Police Station A files an FIR. Police Station B files another. Police Station C files a third.*  
> *Nobody realizes they are connected.*  
> *NEXUS ingests this fragmented data and discovers the hidden web: a shared phone, a shared vehicle caught on a shared CCTV, mapping to a single organized campaign—revealing the mastermind behind all three incidents.*

---

## The Problem It Solves

| Pain Point | NEXUS Solution |
|:---|:---|
| Investigations trapped in departmental silos | Silo Buster cross-jurisdictional graph traversal |
| No real-time workload visibility | Live assignment engine with Gini-balanced distribution |
| Approval bottlenecks with no audit trail | Multi-tier approval workflow + SHA-256 immutable ledger |
| SLA breaches go unnoticed until critical | Automated escalation engine with supervisor delegation |
| Compliance gaps discovered late | Continuous 20-rule policy compliance engine |
| Fragmented notifications across channels | Priority-routed notification hub with digest engine |
| No explainability in AI-linked evidence | XAI provenance chains on every analytical connection |

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        Next.js 14 React Command Center                    │
│                                                                           │
│  Silo Buster Graph   ·   Tactical GIS Map   ·   Investigation Workspace   │
│  Task DAG Engine     ·   Approval Queue     ·   Executive Analytics       │
│  Escalation Monitor  ·   Notification Inbox ·   Audit & Compliance Views  │
└────────────────────────────────┬──────────────────────────────────────────┘
                                 │  JWT REST + WebSocket
┌────────────────────────────────▼──────────────────────────────────────────┐
│                          FastAPI Backend Engine                            │
│                                                                           │
│  ┌─────────────────┐  ┌───────────────────┐  ┌──────────────────────┐    │
│  │ Analytics Engine│  │  Silo Buster      │  │  Task DAG Engine     │    │
│  │ - Entity Res.   │  │  - Neo4j Traversal│  │  - Dependency Graph  │    │
│  │ - DBSCAN        │  │  - PageRank       │  │  - Cycle Detection   │    │
│  │ - CUSUM Anomaly │  │  - XAI Provenance │  │  - SLA Timers        │    │
│  └─────────────────┘  └───────────────────┘  └──────────────────────┘    │
│  ┌─────────────────┐  ┌───────────────────┐  ┌──────────────────────┐    │
│  │ Assignment Eng. │  │  Approval Engine  │  │  Notification Hub    │    │
│  │ - Workload Score│  │  - Multi-Tier     │  │  - Priority Routing  │    │
│  │ - Gini Balance  │  │  - Auto-Delegate  │  │  - Digest Engine     │    │
│  │ - Jurisdiction  │  │  - Expiry Timers  │  │  - Entity Threading  │    │
│  └─────────────────┘  └───────────────────┘  └──────────────────────┘    │
│  ┌─────────────────┐  ┌───────────────────┐  ┌──────────────────────┐    │
│  │ Audit Ledger    │  │ Compliance Engine │  │  Command Center      │    │
│  │ - SHA-256 Chain │  │  - 20 Policy Rules│  │  - Executive KPIs    │    │
│  │ - Masking       │  │  - Risk Score 0-C │  │  - District Health   │    │
│  │ - Integrity API │  │  - Cont. Monitor  │  │  - Live Workload     │    │
│  └─────────────────┘  └───────────────────┘  └──────────────────────┘    │
└──────────┬─────────────────────────────────────────┬───────────────────────┘
           │                                         │
    ┌──────▼──────┐                         ┌────────▼──────┐
    │  PostgreSQL │                         │    Neo4j      │
    │  Relational │                         │  Graph DB     │
    │  + SQLite   │                         │  (Bolt 7687)  │
    │  (Testing)  │                         └───────────────┘
    └─────────────┘
```

### Event-Driven Backbone

All subsystems communicate through a central `EventDispatcher`. Every operational action—task creation, assignment, approval, escalation, notification dispatch—automatically produces:
1. A **SHA-256 hash-chained audit record** (immutable)
2. A **compliance policy evaluation** (deterministic, 20 rules)

Zero manual logging is required from feature teams.

---

## Features

### 🔍 Intelligence & Analytics
- **Entity Resolution** — Jaro-Winkler + phonetic deduplication across FIRs, suspects, vehicles
- **Silo Buster** — Neo4j cross-jurisdictional graph traversal with PageRank mastermind scoring
- **DBSCAN Crime Series** — Spatial clustering of related incidents
- **CUSUM Anomaly Detection** — Temporal spike detection on crime rates
- **XAI Evidence Chains** — Every analytical connection cites explicit evidence

### ⚙️ Operational Command
- **Task DAG Engine** — Dependency-aware task execution with cycle detection and SLA state machines
- **Workload Assignment Engine** — Capability scoring, Gini-balanced distribution, jurisdiction enforcement
- **Multi-Tier Approval Workflow** — Policy-validated approval chains with auto-delegation and expiry
- **Automated Escalation Engine** — SLA breach detection, supervisor delegation, resolution tracking
- **Priority Notification Hub** — 8 digest types, escalating reminders, entity-threaded inbox

### 📊 Visibility & Governance
- **Supervisor Command Center** — Live workload dashboard, officer health monitoring
- **Executive Analytics Dashboard** — District health heatmaps, deterministic KPIs, trend analysis
- **Investigation Workspace** — Collaborative evidence management with activity timeline
- **Immutable Audit Ledger** — SHA-256 hash chaining, sensitive field masking, O(N) integrity sweeps
- **Compliance Monitoring Engine** — 20 deterministic policy rules, subsystem risk scoring (0–100)

---

## Technology Stack

| Layer | Technology |
|:---|:---|
| **Frontend** | Next.js 14, React 18, TypeScript, TanStack Query |
| **Backend** | FastAPI, Python 3.10+, SQLAlchemy 2.0, Pydantic v2 |
| **Relational DB** | PostgreSQL 15 (production), SQLite (testing) |
| **Graph DB** | Neo4j 5.12 (Cypher traversals, APOC) |
| **Auth** | JWT (python-jose), bcrypt password hashing |
| **Real-Time** | FastAPI WebSockets |
| **Rate Limiting** | SlowAPI |
| **Cryptography** | SHA-256 (hashlib) — deterministic hash chaining |
| **Analytics** | scikit-learn (DBSCAN), scipy (CUSUM), jellyfish (phonetics) |
| **Testing** | pytest, httpx, 1,070 automated test cases |
| **Infrastructure** | Docker Compose |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose (for databases)
- Python 3.10+
- Node.js 18+

### 1. Clone & Start Databases
```bash
git clone https://github.com/your-org/nexus.git
cd nexus
docker-compose up -d
```

### 2. Start the Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Seed Demo Dataset
```bash
# From project root — loads Karnataka Police synthetic dataset
python backend/seed_demo.py
```

### 4. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

Navigate to **http://localhost:3000**

---

## Demo Credentials

| Role | Username | Password | Access Level |
|:---|:---|:---|:---|
| Commissioner (Admin) | `admin` | `nexus2026` | Full system access |
| ACP Bangalore | `acp_blr` | `nexus2026` | District command + approvals |
| DCP Operations | `dcp_ops` | `nexus2026` | Escalation + compliance |
| Supervisor | `supervisor_1` | `nexus2026` | Assignment + task oversight |
| Investigating Officer | `officer_1` | `nexus2026` | Investigation workspace |

---

## API Overview

The backend exposes **22 REST routers** and a WebSocket bus at `ws://localhost:8000/ws`.

| Router | Path | Description |
|:---|:---|:---|
| Auth | `/api/auth` | Login, token refresh, user profile |
| Analytics | `/api/analytics` | Entity resolution, clustering, anomalies |
| Intelligence | `/api/intelligence` | Silo Buster, XAI provenance, person graphs |
| Tasks | `/api/tasks` | DAG engine, SLA state machine |
| Assignment | `/api/assignment` | Workload scoring, recommendation, override |
| Governance | `/api/governance` | Rule validation, override rationale |
| Approval | `/api/approval` | Approval queue, multi-tier action, delegation |
| Escalation | `/api/escalation` | SLA monitoring, escalation routing |
| Notification Hub | `/api/notification-hub` | Inbox, digest, reminders, threading |
| Command Center | `/api/command-center` | Supervisor workspace, officer health |
| Executive Dashboard | `/api/executive` | District KPIs, heatmaps, trend analysis |
| Investigation Workspace | `/api/investigation-workspace` | Cases, evidence, collaborators |
| Audit Ledger | `/api/audit` | History, entity trail, integrity verification |
| Compliance | `/api/compliance` | Dashboard, violations, rules, risk, export |

**Interactive API docs**: http://localhost:8000/docs

---

## Folder Structure

```
nexus/
├── backend/
│   ├── analytics/          # Entity resolution, DBSCAN, CUSUM
│   ├── api/routers/        # 22 FastAPI route modules
│   ├── approval/           # Multi-tier approval engine
│   ├── assignment/         # Workload & capability engine
│   ├── audit/              # SHA-256 immutable ledger
│   ├── auth/               # JWT authentication
│   ├── command_center/     # Supervisor & executive dashboards
│   ├── compliance/         # 20-rule compliance engine
│   ├── db/schema.py        # PostgreSQL SQLAlchemy models
│   ├── events/             # EventDispatcher pub/sub backbone
│   ├── intelligence/       # Silo Buster, Neo4j, XAI
│   ├── notification/       # Notification hub & digest engine
│   ├── tests/              # 1,070 automated test cases
│   ├── seed_demo.py        # One-command demo dataset seeder
│   └── main.py             # FastAPI application entry point
├── frontend/
│   ├── components/
│   │   ├── audit/          # Audit timeline & integrity viewer
│   │   ├── compliance/     # Compliance dashboard & risk gauge
│   │   ├── command-center/ # Supervisor command panels
│   │   └── layout/         # Navigation & error boundaries
│   ├── hooks/useApi.ts     # Typed React Query hooks
│   ├── services/apiClient.ts # JWT API gateway
│   └── pages/              # Next.js route pages
├── docs/
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── PERFORMANCE_VALIDATION_REPORT.md
│   ├── PROTOTYPE_READINESS_REPORT.md
│   └── API_CATALOG.md
├── docker-compose.yml       # PostgreSQL + Neo4j containers
├── backend/seed_demo.py     # Demo data generator
└── README.md
```

---

## Performance

All operations meet or exceed production SLA targets, measured on a standard development machine (SQLite in-memory, single process):

| Operation | SLA Target | Achieved |
|:---|:---|:---|
| Workspace Loading | < 50 ms | **14.2 ms** ✅ |
| Task DAG Resolution | < 10 ms | **2.1 ms** ✅ |
| Assignment Recommendation | < 15 ms | **4.8 ms** ✅ |
| Approval Queue Query | < 10 ms | **3.1 ms** ✅ |
| Audit Hash Chaining (per record) | < 10 ms | **1.2 ms** ✅ |
| Cryptographic Chain Sweep (500 records) | < 50 ms | **12.5 ms** ✅ |
| Compliance Rule Evaluation | < 10 ms | **0.9 ms** ✅ |
| Compliance Dashboard Generation | < 75 ms | **18.6 ms** ✅ |
| Report Export (JSON / CSV) | < 100 ms | **8.3 ms** ✅ |

---

## Testing

NEXUS maintains a comprehensive automated test suite across all subsystems:

```bash
# Run full suite
python -m pytest backend/tests/ -q -p no:warnings
# → 1,070 passed in 45.29s

# Run specific subsystems
python -m pytest backend/tests/test_audit_ledger.py       # Audit: 203 tests
python -m pytest backend/tests/test_compliance_engine.py  # Compliance: 225 tests
python -m pytest backend/tests/test_notification_hub.py   # Notifications: 250 tests
python -m pytest backend/tests/test_e2e_workflows.py      # E2E Workflows: 3 tests
```

| Test Module | Tests | Coverage |
|:---|:---|:---|
| Task Engine | 42 | DAG, SLA state machine, cycle detection |
| Workload & Assignment | 103 | Capability scoring, Gini balance, overrides |
| Executive Analytics | 145 | KPIs, heatmaps, trend analysis |
| Approval Workflow | 120 | Multi-tier, delegation, expiry |
| Notification Hub | 250 | Routing, digest, reminders, threading |
| Audit Ledger | 203 | SHA-256 chaining, masking, integrity sweeps |
| Compliance Engine | 225 | 20 rules, risk scoring, RBAC, SLA targets |
| E2E Workflows | 3 | Investigation, Approval, Escalation lifecycles |
| **Total** | **1,070+** | **0 failures** |

---

## Future Roadmap

- **v1.1**: Live CCTNS ETL pipeline integration replacing the synthetic data simulator
- **v1.2**: Mobile command app (React Native) for field officers
- **v2.0**: Federated district deployment with cross-district secure intelligence sharing
- **v2.1**: Predictive patrol deployment using historical crime pattern data

---

## License

MIT License. See [LICENSE](LICENSE).

---

<div align="center">
<sub>Built for the Karnataka State Police Datathon 2026 · NEXUS v1.0.0-rc1</sub>
</div>
