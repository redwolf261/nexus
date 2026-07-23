# NEXUS Demo Guide — 5-Minute Walkthrough Script

> This guide is for presenters. Each step includes what to show, what to say, and why it matters operationally.

---

## Setup (before the demo starts)

```bash
# Start backend
python -m uvicorn backend.main:app --reload

# Seed demo data (if not already seeded)
python backend/seed_demo.py

# Start frontend
cd frontend && npm run dev
```

Navigate to **http://localhost:3000**

---

## Step 1 — Login (30 seconds)

**Show**: Login screen → enter `acp_blr` / `nexus2026`

**Say**: *"NEXUS uses role-based access control. An ACP sees the full operational picture — investigations, assignments, approvals, and compliance. A constable only sees their own workspace. Every API call is JWT-authenticated."*

---

## Step 2 — Executive Dashboard (45 seconds)

**Show**: Navigate to Executive Dashboard

**Say**: *"This is the district health command view. Green means active investigations are on track. The Gini coefficient here measures workload balance across officers — anything above 0.4 triggers automatic rebalancing recommendations. These KPIs refresh in real-time."*

---

## Step 3 — Investigation Workspace (60 seconds)

**Show**: Open Investigation `INV-2026-001 — Operation Cyber Shield`

**Say**: *"Each investigation has a DAG task graph. Task dependencies are enforced — you cannot interrogate a suspect before securing the CCTV footage. Every task carries an SLA timer. Red means breached, amber means warning. The system automatically escalates when timers expire — no one needs to remember to follow up."*

---

## Step 4 — Silo Buster (45 seconds)

**Show**: Navigate to Silo Buster → run analysis for `INV-2026-001`

**Say**: *"This is what makes NEXUS different from a case management system. Three FIRs from three different stations. No human analyst connected them. But they share a phone number — two hops — shared vehicle — one hop — CCTV sighting. The graph reveals the campaign behind all three incidents. Every link cites explicit evidence. No black box."*

---

## Step 5 — Assignment Engine (45 seconds)

**Show**: Open Assignment Panel → view recommendation for TSK-101

**Say**: *"When a task is created, the assignment engine scores every available officer against it: jurisdiction, workload, skill match, active SLA pressure. It recommends the best-fit officer and shows the supervisor exactly why. The supervisor can override with a recorded rationale — which itself becomes an audit entry."*

---

## Step 6 — Approval Workflow (45 seconds)

**Show**: Open Approval Queue → show pending approval for `APP-E2E-200`

**Say**: *"Evidence submissions and override decisions require multi-tier approvals. This one needs Supervisor sign-off, then ACP countersignature. If the Supervisor is unavailable, the system auto-delegates to the ACP with a timestamped delegation record. Nothing slips through."*

---

## Step 7 — Notification Inbox (30 seconds)

**Show**: Open Notification Center

**Say**: *"Officers receive prioritized, threaded notifications — SLA warnings, approval outcomes, escalation alerts, shift digests. They're deduplicated and grouped by entity so an officer doesn't get 15 separate pings about the same investigation."*

---

## Step 8 — Audit Ledger (45 seconds)

**Show**: Open Audit Ledger → show integrity verification result

**Say**: *"Every action in this system — every task creation, assignment, approval decision, notification dispatch — produces a tamper-evident record. Each record is SHA-256 hashed and chained to the previous one. If anyone modifies a record, the chain breaks and the verification sweep catches it instantly. This is the evidence chain that would hold up in court."*

---

## Step 9 — Compliance Dashboard (30 seconds)

**Show**: Open Compliance Dashboard → show risk score and active violations

**Say**: *"The compliance engine continuously evaluates 20 policy rules against live operational data. Right now, one officer is over the maximum workload capacity — that's a medium-severity violation. The system shows the remediation step and flags it for the supervisor. No auditor needs to run a quarterly check — this runs continuously, automatically."*

---

## Closing (30 seconds)

**Say**: *"What you've seen is not a prototype built for a demo. It is a production-quality platform: 1,070 automated tests, all SLA targets met at sub-15ms, full cryptographic audit trail, and one-command deployment. The same architecture that runs this simulation can run against a live CCTNS feed. That is NEXUS."*
