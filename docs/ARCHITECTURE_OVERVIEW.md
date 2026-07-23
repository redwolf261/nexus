# NEXUS Platform Architecture Overview

## Overview
NEXUS is a Palantir-grade tactical intelligence and crime analytics platform built for public sector command centers. It fuses relational databases, graph traversal engines, geospatial maps, task execution DAGs, approval governance, notification hubs, immutable cryptographic audit ledgers, and deterministic compliance monitoring into a single unified platform.

---

## High-Level Topology

```
+------------------------------------------------------------------------------------+
|                               React 18 / Next.js UI                                |
|  - Silo Buster Force Graph      - Tactical GIS Intelligence Map                    |
|  - Investigation Workspace      - Task DAG Engine & Workload Governance            |
|  - Executive Analytics          - Approval & Escalation Monitors                   |
|  - Notification Inbox           - Immutable Audit & Compliance Dashboards          |
+------------------------------------------------------------------------------------+
                                           │
                                           ▼ (JWT Authenticated REST & WebSockets)
+------------------------------------------------------------------------------------+
|                                FastAPI Backend Engine                              |
|  ├── Analytics Engine (Entity Resolution, DBSCAN Crime Series, CUSUM Anomaly)     |
|  ├── Silo Buster Engine (Neo4j Graph Traversals, Link Analysis, XAI Provenance)    |
|  ├── Task Engine (DAG Resolution, Cycle Detection, SLA Timers)                    |
|  ├── Workload & Assignment Engine (Capability Scoring, Gini Balance, Overriding)  |
|  ├── Multi-Tier Approval Engine (Policy Evaluation, Auto-Delegation, Escalation)  |
|  ├── Notification Hub (Orchestrator, Digest Engine, Threading, Reminders)         |
|  ├── Immutable Audit Subsystem (SHA-256 Hash Chaining, Masking, Verification)      |
|  └── Compliance Engine (20+ Deterministic Rules, Risk Scoring 0-100, Monitor)     |
+------------------------------------------------------------------------------------+
                        │                                    │
                        ▼                                    ▼
         +─────────────────────────────+           +───────────────────+
         |   PostgreSQL Relational DB  |           | Neo4j Graph DB    |
         +─────────────────────────────+           +───────────────────+
```

---

## Core Subsystem Index

1. **Analytical Intelligence (Phases 1-7)**:
   - Entity Resolution (Jaro-Winkler + Phonetic Fallback), DBSCAN Spatial Clustering, CUSUM Temporal Anomaly Detection, Neo4j Graph Traversals, XAI Evidence Chains.
2. **Operational Command Engine (Phase 8.1 - 8.3)**:
   - DAG Task Dependency Engine, Workload Governance & Capability Scoring, Executive Analytics & Command Center.
3. **Approval & Escalation Subsystem (Phase 8.4)**:
   - Multi-tier approval routing, policy checks, auto-delegation, and automated SLA breach escalations.
4. **Notification Communication Hub (Phase 8.5)**:
   - Priority routing, 8 deterministic digest types, escalating reminders, entity threading, and interactive inbox.
5. **Immutable Cryptographic Audit Ledger (Phase 8.6 M1)**:
   - SHA-256 hash-chained append-only ledger, context tracking, sensitive data masking, $O(N)$ integrity verification.
6. **Compliance Monitoring Engine (Phase 8.6 M2)**:
   - 20+ deterministic policy rules, subsystem risk scoring (0-100), risk band classification, and continuous background scanner.
