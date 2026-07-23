# NEXUS Phase 8: Operational Command Platform
## Enterprise Architecture Design

**Classification:** Strategic Architecture  
**Scope:** Operational Command & Control Layer  
**Audience:** Police Operations, Implementation Teams, Command Centre Leadership  
**Design Horizon:** 24/7 Operations, 500+ Analysts, 50+ Supervisors, 1000+ Active Cases  

---

# EXECUTIVE CONTEXT

## The Problem Statement

**Current State (Phase 7):**
- NEXUS provides world-class analytical intelligence
- Analysts can generate superior investigative leads
- Quality of intelligence is high
- **But:** No systematic case management, no task coordination, no supervisor oversight, no operational SLAs

**The Gap:**
A State Police Command Centre with 500 analysts needs to:
1. Assign cases to analysts based on workload & skills
2. Track investigation progress in real-time
3. Escalate stalled cases before they breach SLAs
4. Ensure supervisors have complete operational visibility
5. Prevent duplicate work, lost cases, missed deadlines
6. Coordinate across jurisdictions and shifts
7. Make evidence collection systematic, not ad-hoc
8. Audit every investigative decision

**The Consequence of Not Solving This:**
- Cases slip through cracks (no tracking)
- Duplicate investigations (no coordination)
- Burnout (no workload balancing)
- Missed SLAs (no escalation)
- Inconsistent quality (no supervisor review)
- No audit trail (legal liability)

**Phase 8 Objective:**
Transform NEXUS from an analytical tool into an operational command platform where human supervisors maintain strategic control over investigation operations at scale.

---

# DELIVERABLE 1: OPERATIONAL CAPABILITY MAP

## Investigation Operations Domain

### Capability: Case Assignment

**Purpose:**  
Systematically allocate FIRs to analysts based on workload, skills, jurisdiction, and case complexity.

**Primary Users:**  
Supervisors, Command Centre Operators

**Current Platform Support:**  
- ❌ No case assignment mechanism
- ❌ No workload tracking
- ❌ No skill-based routing
- ✅ Investigations exist in database (Phase 2)

**Gap Analysis:**
- Manual assignment (phone call, message)
- No visibility into why cases assigned to specific analysts
- No prevention of overload
- No skill matching (can't tell if analyst has cyber crime experience)
- Assignments lost if supervisor exits system

**Priority:** CRITICAL (blocks all downstream operations)

**Dependencies:**
- Task engine (Deliverable 6)
- Officer profile data (skill tags, jurisdiction, max capacity)
- Supervisor permissions model

**Expected Outcome:**
- Supervisor opens "Assignment Queue" (FIRs awaiting assignment)
- System suggests analyst based on: workload (< 8 cases), skill match, jurisdiction
- Supervisor clicks assign or picks different analyst
- Analyst receives task in their queue
- System audits all assignments with reasoning

---

### Capability: Case Triage & Priority

**Purpose:**  
Auto-classify new cases by risk level to route critical cases to senior analysts.

**Primary Users:**  
Supervisors, Senior Analysts

**Current Platform Support:**  
- ✅ Risk scoring exists (Phase 7: gang crime flag, severity)
- ❌ No triage workflow
- ❌ No priority queue

**Gap Analysis:**
- FIRs arrive without priority context
- All cases treated equally regardless of risk
- No auto-escalation for high-risk cases (kidnapping, terrorism)
- Supervisors can't quickly see "what needs immediate attention"

**Priority:** HIGH (enables effective resource allocation)

**Dependencies:**
- Risk model (Phase 7)
- Case priority taxonomy (critical, high, medium, low)
- Supervisor override mechanism

**Expected Outcome:**
- New FIR arrives → Auto-scored by risk model
- If risk_score > 0.85: flag as CRITICAL, notify supervisor immediately
- If gang-related: HIGH priority, route to gang investigation specialist
- If missing person > 72 hours: CRITICAL, escalate to DCP
- Supervisor can override priority based on operational context

---

### Capability: Investigation Lifecycle Management

**Purpose:**  
Track investigation from creation through closure with clear state transitions.

**Primary Users:**  
Analysts, Supervisors

**Current Platform Support:**  
- ✅ Investigation entity exists (Phase 2)
- ❌ No state machine
- ❌ No closure workflow
- ❌ No re-open capability

**Gap Analysis:**
- Investigations can get "stuck" without clear path to resolution
- No distinction between "active", "awaiting review", "closed"
- Can't quickly find investigations awaiting action
- No audit trail of why investigation was closed

**Priority:** HIGH

**Dependencies:**
- Investigation status model
- Supervisor review workflow
- Evidence validation before closure

**Expected Outcome:**
- Investigation states: CREATED → ASSIGNED → ACTIVE → AWAITING_REVIEW → CLOSED
- Each transition audited with timestamp and user
- Analyst can't close investigation; requires supervisor review
- Supervisor sees investigation age, pending tasks, missing evidence
- Closure requires: summary, evidence count, investigative outcome (solved, unsolved, false lead, etc.)

---

### Capability: Evidence Workflow Orchestration

**Purpose:**  
Manage systematic collection, validation, and linking of evidence to investigations.

**Primary Users:**  
Analysts, Evidence Managers, Supervisors

**Current Platform Support:**  
- ✅ Evidence entity exists (Phase 7)
- ❌ No workflow
- ❌ No collection tracking
- ❌ No validation SLA

**Gap Analysis:**
- Evidence scattered across multiple systems (CCTV database, phone records, property)
- No visibility into evidence collection progress
- Evidence linked manually (ad-hoc)
- Can't tell which cases have complete evidence vs. partial

**Priority:** HIGH (impacts case closure rate)

**Dependencies:**
- Evidence model enhancement
- Integration points (CCTV system, telecom providers, bank records)
- Evidence checklist by case type

**Expected Outcome:**
- Investigation created → Auto-generate evidence checklist based on case type
  - For murder: need autopsy, crime scene photos, witness statements, ballistics
  - For cybercrime: need logs, forensic disk image, communication transcripts
- Analyst marks evidence as "requested", "received", "verified"
- System tracks collection SLA (e.g., ballistics must arrive within 10 days)
- Dashboard shows investigation completeness: "4/8 evidence items collected"
- Supervisor gets alert if critical evidence missing beyond SLA

---

## Officer Operations Domain

### Capability: Officer Workload Management

**Purpose:**  
Ensure analysts don't exceed sustainable workload; balance based on case complexity.

**Primary Users:**  
Supervisors, Command Centre

**Current Platform Support:**  
- ❌ No workload tracking
- ❌ No capacity model
- ❌ No saturation alerts

**Gap Analysis:**
- Supervisors have no visibility into individual analyst workload
- Senior analysts get overloaded; junior analysts underutilized
- No mechanism to redistribute work
- Burnout risk invisible until analyst quits

**Priority:** HIGH (operational sustainability)

**Dependencies:**
- Officer profile entity (max capacity, current load)
- Case complexity scoring
- Workload balancing algorithm

**Expected Outcome:**
- Supervisor dashboard shows per-analyst: "Analyst A: 12 cases (max 10) - OVERLOADED"
- Case complexity weights: simple fraud = 1x, gang investigation = 3x, serial murder = 5x
- System prevents new assignment if: (current_cases + case_weight) > max_capacity
- Supervisor can override or redistribute existing cases
- KPI: analyst average workload 7 cases (sustainable range 6-9)

---

### Capability: Officer Shift Management

**Purpose:**  
Track analyst availability across shifts; ensure coverage for critical cases.

**Primary Users:**  
Command Centre, Supervisors

**Current Platform Support:**  
- ❌ No shift tracking
- ❌ No on-call system
- ❌ No handover mechanism

**Gap Analysis:**
- No visibility into who's working when
- Cases assigned to offline analyst (must wait for next shift)
- Critical cases have no night-shift coverage
- Handovers informal (lost context)

**Priority:** MEDIUM (improves operational continuity)

**Dependencies:**
- Officer shift entity
- Shift roster management
- On-call escalation model

**Expected Outcome:**
- Shift roster: Monday-Friday 9-5, Supervisor A; 6-10pm, Supervisor B; Night on-call
- When supervisor assigns case at 11pm: if all day-shift analysts offline, auto-escalate to on-call
- Case handover form: outgoing analyst summarizes findings, flags risks, for incoming analyst
- Dashboard shows: "Critical case with night-shift coverage: YES" or "NO - will escalate tomorrow"

---

### Capability: Officer Capability Tracking

**Purpose:**  
Maintain officer skills, certifications, jurisdiction expertise for optimal assignments.

**Primary Users:**  
HR, Supervisors, Command Centre

**Current Platform Support:**  
- ❌ No skill database
- ❌ No competency tracking
- ❌ No expertise matching

**Gap Analysis:**
- Supervisor can't tell if analyst has cyber crime training
- Senior analysts buried in routine cases instead of complex investigations
- Difficult to know which analysts can work in which jurisdictions
- Specialized training (counter-terrorism, financial crimes) not tracked

**Priority:** MEDIUM (enables expert deployment)

**Dependencies:**
- Officer profile enhancement (skills array, certifications, jurisdictions)
- Training record entity
- Supervisor feedback on analyst performance

**Expected Outcome:**
- Officer record: skills tags ["cyber-crime", "gang-investigation", "missing-persons"], certifications ["forensic-photography", "undercover"], jurisdiction ["bangalore", "karnataka"]
- Supervisor assigning kidnapping case gets: "Analyst A (suitable: yes - missing-persons expert, bangalore jurisdiction)"
- Training tracked: "Analyst B completed cyber-crime course on 2026-06-15"
- KPI: expertise utilization (% of cases assigned to matched specialist)

---

## Command Centre Domain

### Capability: Supervisor Operational Dashboard

**Purpose:**  
Single-pane-of-glass for command centre supervisors to manage operations.

**Primary Users:**  
Supervisors, DCP, ACP

**Current Platform Support:**  
- ❌ No dashboard
- ❌ No real-time case visibility
- ❌ No alert aggregation

**Gap Analysis:**
- Supervisors have no centralized operational view
- Must context-switch between multiple systems (FIR database, intelligence platform, case tracker)
- Can't quickly answer: "What's the most critical case right now?"
- No visibility into analyst productivity, SLA health, escalations

**Priority:** CRITICAL (enables command and control)

**Dependencies:**
- Task engine, assignment system, SLA tracking, escalation engine
- Real-time data aggregation
- Multi-level role permissions

**Expected Outcome:**
See Deliverable 5 (detailed design follows)

---

### Capability: Inter-shift Handover

**Purpose:**  
Ensure critical case context transfers between shifts without information loss.

**Primary Users:**  
Supervisors, Analysts

**Current Platform Support:**  
- ❌ No handover mechanism
- ❌ No standardized format

**Gap Analysis:**
- Outgoing supervisor doesn't brief incoming supervisor
- Critical developments missed by night team
- No record of what decisions were made overnight
- Operational history invisible across shifts

**Priority:** MEDIUM (prevents blind spots)

**Dependencies:**
- Shift management entity
- Handover workflow
- Investigation summary entity

**Expected Outcome:**
- 30 minutes before shift end: outgoing supervisor opens "Shift Handover"
- System shows: new cases (5), escalations (2), pending approvals (3), blocked cases (1)
- Supervisor writes: "Kidnapping case (K-001) - suspect identified, awaiting extradition documents, expedited. Missing-person case (M-015) - body found, awaiting family confirmation."
- Incoming supervisor reviews handover before taking command
- Handover logged as audit trail

---

## Supervision Domain

### Capability: Supervisor Approval Workflow

**Purpose:**  
Ensure critical decisions (case closure, high-risk actions) reviewed by supervisor before execution.

**Primary Users:**  
Supervisors, Analysts

**Current Platform Support:**  
- ✅ Entity merge approval exists (Phase 7.3)
- ❌ No general approval workflow
- ❌ No approval SLA

**Gap Analysis:**
- Analysts can take risky actions without review (wrong entity merge could contaminate investigation)
- No standardized approval process
- Supervisor must manually check every case closure
- Approval delays can slow investigation

**Priority:** HIGH (operational safety)

**Dependencies:**
- Approval workflow engine
- Supervisor queue entity
- Escalation on approval timeout

**Expected Outcome:**
- Analyst completes investigation summary, requests closure
- Supervisor gets approval task: "Review case K-001 closure"
- Supervisor reviews: evidence count, investigation outcome, recommendation, linked FIRs
- Supervisor can: APPROVE, REQUEST_REVISION, or REJECT
- If not approved within 24 hours: auto-escalate to ACP
- Audit trail records: who approved, when, any comments

---

### Capability: Escalation Management

**Purpose:**  
Auto-escalate stalled cases, SLA breaches, and high-risk situations to senior leadership.

**Primary Users:**  
Supervisors, ACP, DCP

**Current Platform Support:**  
- ❌ No escalation engine
- ❌ No SLA tracking
- ❌ No auto-escalation

**Gap Analysis:**
- Cases get forgotten if analyst distracted
- Supervisors reactive (learn about problem after breach)
- No mechanism to push critical issues to command
- High-risk cases invisible to senior leadership

**Priority:** CRITICAL (prevents operational failures)

**Dependencies:**
- SLA definition entity
- Escalation rule engine
- Notification system

**Expected Outcome:**
- SLA defined: missing person must have 5 evidence items within 48 hours
- Case missing person at 47 hours with 2 evidence items → auto-escalate to supervisor
- Supervisor sees: "⚠️ HIGH RISK: M-001 approaching SLA breach (1 hour remaining)"
- If not resolved by SLA deadline → auto-escalate to ACP
- Pattern detected: 3 cases escalated this week → trend alert to DCP

---

### Capability: Analyst Performance Review

**Purpose:**  
Track analyst performance against operational KPIs for coaching and evaluation.

**Primary Users:**  
Supervisors, HR, ACP

**Current Platform Support:**  
- ❌ No performance tracking
- ❌ No KPI aggregation

**Gap Analysis:**
- Supervisor has no data on analyst productivity
- Performance evaluations based on informal impressions
- Can't identify struggling analysts before burnout
- Can't recognize high performers for promotion

**Priority:** MEDIUM (enables people management)

**Dependencies:**
- KPI calculation engine (average case age, SLA compliance, escalation rate, etc.)
- Performance scoring model

**Expected Outcome:**
- Monthly performance report per analyst:
  - Cases assigned: 8
  - Cases closed: 6
  - Avg investigation age: 18 days (target 21)
  - SLA compliance: 95% (target 98%)
  - Escalations: 1 (low - good)
  - Supervisor feedback: "Strong evidence collection, needs help with coordination"
- Trend analysis: is performance improving or declining?

---

## Task Management Domain

### Capability: Task Assignment & Tracking

**Purpose:**  
Create and manage discrete tasks within investigations (collect evidence, contact witness, obtain warrant).

**Primary Users:**  
Analysts, Supervisors

**Current Platform Support:**  
- ❌ No task entity
- ❌ No task assignment
- ❌ No task tracking

**Gap Analysis:**
- Investigations don't break down into manageable tasks
- Analyst must mentally track what needs to happen next
- No visibility into task completion status
- Tasks can be forgotten if analyst distracted

**Priority:** CRITICAL (enables investigation execution)

**Dependencies:**
- Task entity (Deliverable 6)
- Task lifecycle engine
- Task history logging

**Expected Outcome:**
See Deliverable 6 (detailed design follows)

---

### Capability: Task Dependency Management

**Purpose:**  
Prevent tasks from executing out of order; enforce logical investigation flow.

**Primary Users:**  
Analysts, Supervisors

**Current Platform Support:**  
- ❌ No dependency tracking

**Gap Analysis:**
- Tasks executed in wrong order (e.g., analyst requests arrest warrant before identity confirmed)
- No mechanism to enforce logical flow
- Rework required when prerequisites not met

**Priority:** MEDIUM

**Dependencies:**
- Task dependency model
- Task validation engine

**Expected Outcome:**
- Investigation task graph: "Collect evidence" (must complete before) "Request warrant" (must complete before) "Execute arrest"
- System prevents "Request warrant" if "Collect evidence" not yet marked complete
- Analyst sees: "Task unavailable: requires 'Collect DNA evidence' to complete first"

---

### Capability: Recurring Task Automation

**Purpose:**  
Automatically create recurring tasks (check case status, contact witness for follow-up).

**Primary Users:**  
Supervisors, System

**Current Platform Support:**  
- ❌ No recurring task capability

**Gap Analysis:**
- Cases require periodic check-ins (e.g., every 7 days)
- Must manually create follow-up tasks
- Easy to forget recurring actions

**Priority:** LOW (convenience feature)

**Dependencies:**
- Task recurring rule entity
- Task scheduler

**Expected Outcome:**
- Supervisor creates recurring task: "Check case status - daily for first week, then weekly"
- System auto-creates task every day for 7 days, then every week
- Analyst marks complete each day; system auto-creates next instance

---

## SLA Monitoring Domain

### Capability: SLA Definition & Tracking

**Purpose:**  
Define and monitor operational SLAs (case closure time, evidence collection time, approval time).

**Primary Users:**  
Supervisors, Command Centre, Quality Assurance

**Current Platform Support:**  
- ❌ No SLA framework

**Gap Analysis:**
- No defined standards for case closure time
- No visibility into compliance
- Cases slip through without urgency
- Quality variable based on analyst and supervisor discretion

**Priority:** HIGH (enables operational standards)

**Dependencies:**
- SLA entity, SLA violation tracking
- Compliance reporting

**Expected Outcome:**
- SLAs defined by case type:
  - Murder: 30 days average investigation, 60 day closure
  - Missing person < 24 hrs: 14 days average, 30 day closure
  - Robbery: 20 days average, 45 day closure
  - Cyber fraud: 25 days average, 50 day closure
- System tracks actual vs. target for every case
- Weekly report: "SLA compliance: 94% (target 98%)"
- Automated alerts: cases approaching breach

---

### Capability: SLA Violation Escalation

**Purpose:**  
Automatically escalate cases approaching or breaching SLA deadline.

**Primary Users:**  
Supervisors, ACP

**Current Platform Support:**  
- ❌ No escalation mechanism

**Gap Analysis:**
- Breaches discovered after deadline
- No visibility into at-risk cases
- Reactive problem-solving instead of proactive

**Priority:** CRITICAL

**Dependencies:**
- SLA tracking, escalation engine, notification system

**Expected Outcome:**
- Case SLA: 30 days from assignment
- Day 25: analyst gets notification "5 days to SLA deadline"
- Day 29: supervisor gets alert "Case approaching SLA breach tomorrow"
- Day 30: case auto-escalates to ACP with summary of investigation status
- Post-mortem: if case breaches SLA, root cause documented (insufficient evidence, analyst unavailable, etc.)

---

## Notification & Escalation Domain

### Capability: Real-time Notifications

**Purpose:**  
Deliver time-critical information to analysts and supervisors (new case, escalation, approval needed).

**Primary Users:**  
All operational users

**Current Platform Support:**  
- ❌ No notification system

**Gap Analysis:**
- Users must manually check platform for updates
- Critical alerts missed
- No priority differentiation
- No delivery guarantees

**Priority:** CRITICAL (enables responsiveness)

**Dependencies:**
- Notification system (Deliverable 7)
- Delivery channel management (in-app, email, SMS)
- User notification preferences

**Expected Outcome:**
See Deliverable 7 (detailed design follows)

---

### Capability: Notification Acknowledgement & Read Receipts

**Purpose:**  
Ensure critical notifications are read and acted upon; track operational response time.

**Primary Users:**  
Supervisors, Command Centre

**Current Platform Support:**  
- ❌ No ack system

**Gap Analysis:**
- No visibility into whether notification was read
- Can't tell if analyst saw urgent message
- No tracking of response time

**Priority:** HIGH (accountability and auditability)

**Dependencies:**
- Notification entity with ack status
- Read receipt tracking
- Mean time to acknowledgement KPI

**Expected Outcome:**
- Notification arrives: "New kidnapping case K-001"
- System tracks: sent at 14:32, read at 14:34 (2 min response), acknowledged at 14:36 (assignment accepted)
- If not acknowledged within 30 minutes: auto-escalate to supervisor
- KPI: mean time to acknowledgement (target < 5 min for CRITICAL)

---

## Evidence & Investigation Domain

### Capability: Evidence Chain of Custody

**Purpose:**  
Maintain complete audit trail of evidence access for legal proceedings.

**Primary Users:**  
Analysts, Evidence Managers, Legal

**Current Platform Support:**  
- ✅ Evidence entity exists (Phase 7)
- ❌ No chain of custody tracking
- ❌ No access audit log

**Gap Analysis:**
- Evidence access not audited
- Can't prove evidence integrity in court
- Legal liability exposure

**Priority:** CRITICAL (legal requirement)

**Dependencies:**
- Evidence access log entity
- Audit trail per evidence item
- Digital signature capability (for sensitive evidence)

**Expected Outcome:**
- Every access to evidence logged: who, when, why
- Evidence summary shows: "Accessed 3 times: analyst (view), supervisor (review), legal (court prep)"
- Chain of custody printable for court proceedings
- Analyst can't delete evidence (immutable once created)
- Only authorized users can modify evidence metadata

---

### Capability: Cross-Case Evidence Linking

**Purpose:**  
Identify and link evidence that appears in multiple investigations.

**Primary Users:**  
Analysts, Supervisors

**Current Platform Support:**  
- ❌ No cross-case linking
- ❌ No duplicate detection

**Gap Analysis:**
- Same evidence (vehicle, weapon, suspect) investigated in isolation
- Crime series undetected (different analysts working same gang separately)
- Operational opportunity cost (duplication)

**Priority:** HIGH (enables intelligence synthesis)

**Dependencies:**
- Evidence deduplication engine (leverage Phase 7 entity resolution)
- Cross-case evidence linking UI

**Expected Outcome:**
- System finds: same license plate in 3 different robbery cases
- Alert: "Vehicle VEH-001 (silver Maruti) appears in cases R-001, R-005, R-012"
- Analyst can link cases: merge into gang investigation
- Enables discovery of crime series

---

## Reporting & Analytics Domain

### Capability: Operational Dashboarding

**Purpose:**  
Provide real-time operational metrics for supervisors and command centre.

**Primary Users:**  
Supervisors, ACP, DCP, Command Centre

**Current Platform Support:**  
- ❌ No operational dashboard
- ✅ Intelligence dashboards exist (Phase 7)

**Gap Analysis:**
- No real-time case counts, workload distribution, SLA compliance
- Supervisors can't answer: "How many cases are we investigating right now?"
- DCP has no visibility into operational health

**Priority:** CRITICAL (enables command oversight)

**Dependencies:**
- Real-time metrics aggregation
- Dashboard entity, widget system

**Expected Outcome:**
See Deliverable 5 (detailed design follows)

---

### Capability: Compliance & Audit Reporting

**Purpose:**  
Generate reports for internal audit, legal, and oversight bodies.

**Primary Users:**  
Quality Assurance, Legal, Compliance, Internal Audit

**Current Platform Support:**  
- ❌ No compliance reporting

**Gap Analysis:**
- No documented evidence of investigative procedures followed
- Legal liability if audit questioned investigative decisions
- Can't demonstrate SLA compliance to oversight bodies

**Priority:** MEDIUM (risk management)

**Dependencies:**
- Audit trail completeness, compliance rule engine

**Expected Outcome:**
- Monthly audit report:
  - Cases investigated: 500
  - Cases closed: 300
  - SLA compliance: 96%
  - Escalations reviewed: 45
  - Approvals denied: 2 (documented why)
  - Evidence integrity: 100% (no unauthorized access)

---

## Knowledge Management Domain

### Capability: Investigation Template Library

**Purpose:**  
Provide standardized investigation templates by case type to ensure consistency.

**Primary Users:**  
Analysts, Supervisors

**Current Platform Support:**  
- ❌ No template system

**Gap Analysis:**
- Each analyst investigates differently
- Junior analysts don't know standard procedure
- Investigation quality highly variable
- Difficult to scale to new analysts

**Priority:** MEDIUM (improves consistency and training)

**Dependencies:**
- Template entity, investigation template application workflow

**Expected Outcome:**
- Supervisor creates template for "kidnapping investigation"
  - Mandatory evidence: victim ID, threat communication, demand details, location info
  - Typical tasks: secure family contact, negotiate terms, involve FBI if interstate
  - Investigation duration: typically 5-10 days
- New analyst investigating kidnapping: system prompts "Use kidnapping template? Yes/No"
- Template provides guidance without prescribing rigid process

---

### Capability: Case Playbooks

**Purpose:**  
Capture investigative approaches, lessons learned, best practices by case type.

**Primary Users:**  
Senior Analysts, Supervisors, Training

**Current Platform Support:**  
- ❌ No playbook system

**Gap Analysis:**
- Investigative knowledge siloed with senior analysts
- New analysts must learn from scratch
- Best practices not documented

**Priority:** LOW (continuous improvement)

**Dependencies:**
- Playbook entity, knowledge base system

**Expected Outcome:**
- Playbook: "Gang Investigation - 3 Month Campaign"
  - Phases: intelligence gathering (week 1-4), suspect identification (week 5-8), evidence collection (week 9-12), prosecution prep (week 13+)
  - Typical challenges: witness intimidation, evolving gang structure, multiple crimes per member
  - Resource requirements: 3-5 analysts, 2 supervisors, external coordination (CCTV, telecom)

---

# DELIVERABLE 2: OPERATIONAL WORKFLOW CATALOGUE

## Workflow 1: New FIR Arrival & Initial Triage

```
┌─ FIR ARRIVES (from any source: station, online, tip)
│
├─ AUTO-TRIAGE
│  ├─ Risk scoring (Phase 7 model)
│  ├─ Case type classification
│  ├─ Priority assignment (CRITICAL/HIGH/MEDIUM/LOW)
│  └─ SLA assignment based on case type
│
├─ PRIORITY GATE
│  ├─ CRITICAL (risk_score > 0.85): immediate supervisor notification
│  ├─ HIGH (gang-related, serial): notify supervisor within 15 min
│  ├─ MEDIUM: notify supervisor within 1 hour
│  └─ LOW: add to assignment queue
│
├─ SUPERVISOR REVIEW (for CRITICAL/HIGH only)
│  ├─ Review FIR details
│  ├─ Approve priority or override
│  ├─ Flag for inter-agency coordination if needed
│  └─ Create incident record if pattern detected
│
├─ ASSIGNMENT PHASE
│  ├─ Suggest analyst (workload, skill, jurisdiction)
│  ├─ Supervisor assigns or manually selects
│  ├─ Analyst receives in queue (notification)
│  └─ Investigation created, linked to FIR
│
├─ INVESTIGATION INITIATION
│  ├─ Auto-generate task list from template (if available)
│  ├─ Create evidence checklist by case type
│  ├─ Set investigation status to ACTIVE
│  ├─ Audit log: who assigned, when, justification
│  └─ SLA timer starts
│
└─ HANDOFF TO ANALYST
   └─ Analyst begins investigation tasks
```

**Manual Steps:**
- Supervisor review for CRITICAL cases
- Supervisor assignment decision (can override system suggestion)

**Automatable Steps:**
- Risk scoring (Phase 7)
- Priority assignment
- Case type classification
- Analyst suggestion (based on workload/skill)
- Task list generation
- Evidence checklist generation

**Decision Points:**
- Is priority correct? (supervisor override)
- Is suggested analyst appropriate? (supervisor can pick different analyst)
- Should this case be linked to existing investigation? (pattern detection)

**Failure Points:**
- No analyst available (all at capacity) → escalate to ACP for resource approval
- Duplicate case already open → merge investigations
- Conflicting jurisdiction → escalate for coordination

**Audit Requirements:**
- Who assigned case and when
- Why priority assigned (scoring model output)
- Justification if supervisor overrode assignment suggestion
- All task creation and completion

---

## Workflow 2: Investigation Execution & Evidence Collection

```
┌─ ANALYST RECEIVES INVESTIGATION TASK
│
├─ REVIEW PHASE
│  ├─ Read FIR details
│  ├─ Review intelligence from Phase 7 (linked entities, crime series, etc.)
│  ├─ Review evidence checklist
│  ├─ Identify missing evidence
│  └─ Create action plan
│
├─ EVIDENCE COLLECTION PHASE (iterative)
│  ├─ Task: collect physical evidence
│  │  ├─ Request evidence from collection unit
│  │  ├─ Track status: requested → received → verified
│  │  ├─ SLA: physical evidence within 5 days
│  │  └─ Flag if not received
│  │
│  ├─ Task: obtain witness statements
│  │  ├─ Contact witness (phone/visit)
│  │  ├─ Conduct interview
│  │  ├─ Document statement
│  │  ├─ SLA: primary witness within 3 days
│  │  └─ Escalate if witness unavailable
│  │
│  ├─ Task: collect CCTV footage
│  │  ├─ Identify relevant cameras (location, time window)
│  │  ├─ Request footage from Property
│  │  ├─ Review footage, mark relevant clips
│  │  ├─ SLA: footage obtained within 7 days
│  │  └─ Auto-escalate if camera not recording
│  │
│  ├─ Task: coordinate inter-agency (telecom records, etc.)
│  │  ├─ File formal request
│  │  ├─ Track request status
│  │  ├─ SLA: records obtained within 10 days
│  │  └─ Escalate if delays
│  │
│  └─ Task: obtain warrant (if needed)
│     ├─ Prepare warrant application
│     ├─ Supervisor review & approval (decision point)
│     ├─ Submit to court
│     ├─ Track approval status
│     └─ SLA: warrant within 3 days of application
│
├─ INVESTIGATION UPDATES (continuous)
│  ├─ Log investigative findings
│  ├─ Link to Phase 7 intelligence (entities, patterns)
│  ├─ Update evidence status
│  ├─ Identify new persons of interest
│  └─ Every 3 days: update supervisor (status check-in)
│
├─ SUPERVISOR OVERSIGHT (continuous)
│  ├─ Monitor task completion
│  ├─ Watch for SLA breaches (alert at 80% of SLA)
│  ├─ Escalate stalled tasks
│  ├─ Approve warrant requests
│  └─ Provide guidance if analyst stuck
│
├─ COMPLETION PHASE
│  ├─ Evidence checklist review (all critical items collected?)
│  ├─ Investigation summary drafting
│  ├─ Formal closure request to supervisor
│  └─ Request supervisor approval
│
└─ SUPERVISOR REVIEW & CLOSURE
   ├─ Validate evidence completeness
   ├─ Review investigation summary
   ├─ Determine outcome (solved/unsolved/cold/false lead)
   ├─ Approve or request revision
   └─ Set investigation status to CLOSED
```

**Manual Steps:**
- Analyst task execution (evidence collection, interviews, reviews)
- Supervisor approval for warrants
- Supervisor closure review

**Automatable Steps:**
- Task creation from template
- SLA calculation and breach detection
- Notification/escalation on SLA breach
- Evidence status aggregation

**Decision Points:**
- Is warrant justified? (supervisor decision)
- Is evidence complete? (supervisor decision)
- Can investigation be closed? (supervisor decision)
- Should this investigation link to another? (pattern analysis)

**Failure Points:**
- Witness unavailable/refuses statement → escalate, consider alternative approaches
- Evidence not located (lost crime scene) → document, adjust investigation scope
- External system down (CCTV system outage) → delay SLA, escalate
- Analyst sick/unavailable → reassign tasks, extend SLA
- Conflicting evidence → analyst must reconcile

**Audit Requirements:**
- Every task completion logged with timestamp and evidence attachment
- Every evidence collection tracked (who requested, when arrived, who verified)
- Supervisor approvals documented
- All delays/escalations recorded
- Final closure summary and outcome

---

## Workflow 3: Missing Person Investigation (< 72 Hours)

```
┌─ MISSING PERSON FIR ARRIVES
│
├─ AUTO-PRIORITY: CRITICAL (missing < 72 hrs)
│
├─ IMMEDIATE ACTIONS (first 2 hours)
│  ├─ Auto-assign to senior analyst (skill: missing persons)
│  ├─ Supervisor gets immediate notification
│  ├─ Auto-generate critical task list:
│  │  ├─ Verify person actually missing (contact family)
│  │  ├─ Secure recent photos
│  │  ├─ Create missing person alert
│  │  ├─ Distribute to public (media, social)
│  │  ├─ Check hospital records (unidentified patients)
│  │  └─ Check CCTV (last location)
│  │
│  └─ Supervisor approves alert parameters (age, location, description)
│
├─ INVESTIGATION PHASE (72-hour window)
│  ├─ Intensive task execution
│  ├─ Multiple teams: search (field), intelligence (CCTV/records), family liaison
│  ├─ Daily briefings to supervisor
│  ├─ Real-time escalation if threat detected (abduction, suicide risk)
│  └─ Evidence collection: phone records, transactions, last known location
│
├─ 72-HOUR DECISION GATE
│  ├─ Has person been found?
│  │  ├─ YES → investigation outcome: found safe / found injured / deceased
│  │  └─ NO → escalate to ACP, activate expanded search resources
│  │
│  ├─ Is this suspected abduction/kidnapping?
│  │  └─ YES → upgrade to kidnapping investigation, FBI coordination
│  │
│  └─ Is this suspected suicide/self-harm?
│     └─ YES → search team focus, crisis resources
│
└─ POST-72-HOUR TRANSITION
   ├─ If found: closure process
   ├─ If not found: escalate to ACP, activate statewide search
   └─ Create cold case file for ongoing monitoring
```

**Manual Steps:**
- Supervisor approval of alert parameters
- Family interviews (establish timeline)
- Search team coordination
- 72-hour gate decision

**Automatable Steps:**
- Priority auto-assignment to CRITICAL
- Task list generation (standard missing person template)
- CCTV retrieval request
- Hospital/morgue record checks
- Phone record requests
- 72-hour escalation reminder

**Decision Points:**
- Is this genuinely missing person or voluntary absence? (family/police consensus)
- Is abduction likely? (evidence assessment)
- Should public alert be issued? (risk of publicity vs. search effectiveness)
- Should search expand beyond local? (72-hour gate)

**Failure Points:**
- Family missing from contact (can't verify timeline) → use last known contact
- CCTV footage missing/corrupted → escalate to search team
- Person found but injured → transition to medical/criminal investigation
- Insufficient public response → escalate to media relations

**Audit Requirements:**
- Timeline of all actions (must show "rapid response" protocol followed)
- Supervisor approvals for each escalation
- Inter-agency coordination logs
- Media communications
- Final outcome and closure justification

---

## Workflow 4: Gang Investigation (Multi-Case, Multi-Month)

```
┌─ PATTERN DETECTED: Multiple robberies, same MO, same area
│  (Phase 7 crime series detection triggers)
│
├─ INVESTIGATION INITIATION
│  ├─ Supervisor reviews series detection (are cases truly linked?)
│  ├─ Creates "gang investigation" parent case
│  ├─ Links 5+ related FIRs to parent case
│  ├─ Assigns senior analyst team (2-3 analysts)
│  ├─ Allocates extended SLA (60-90 days)
│  └─ Creates complex task structure (phases: intelligence → identification → evidence → prosecution prep)
│
├─ PHASE 1: INTELLIGENCE GATHERING (Weeks 1-4)
│  ├─ Collect data on crime pattern
│  │  ├─ Analyze MO across cases (methods, timing, location, targets)
│  │  ├─ Interview victims for perpetrator descriptions
│  │  ├─ Map crime locations (Phase 7 spatial analytics)
│  │  ├─ Identify crime corridors (escape routes)
│  │  └─ Link to Phase 7 intelligence (gang networks, associates)
│  │
│  ├─ Community intelligence
│  │  ├─ Informant tips (coordinate with Phase 7 informant system)
│  │  ├─ Street-level contacts
│  │  ├─ Gang member monitoring
│  │  └─ Social media intelligence
│  │
│  └─ Supervisor checkpoint (weekly)
│     └─ Review intelligence quality, redirect if needed
│
├─ PHASE 2: PERPETRATOR IDENTIFICATION (Weeks 5-8)
│  ├─ Suspect identification (from crime scene descriptions)
│  │  ├─ Cross-check with Phase 7 gang member database
│  │  ├─ Use facial recognition on CCTV
│  │  ├─ Build suspect profiles
│  │  └─ Prioritize by likelihood and criminal history
│  │
│  ├─ Evidence linkage
│  │  ├─ Weapons: forensics on firearms from crime scenes
│  │  ├─ Vehicles: ANPR data, CCTV vehicle ID
│  │  ├─ Phones: CDR data linking suspects
│  │  └─ Gang symbols: tattoos, clothing, communication style
│  │
│  ├─ Supervisor decision
│  │  ├─ Are suspects sufficiently identified?
│  │  ├─ Proceed to arrests or continue gathering evidence?
│  │  └─ Coordinate with field operations for surveillance if needed
│  │
│  └─ Decision gate
│     ├─ Strong evidence → proceed to Phase 3
│     └─ Weak evidence → extend Phase 1/2, request additional resources
│
├─ PHASE 3: EVIDENCE COLLECTION (Weeks 9-12)
│  ├─ Warrant applications (supervisor approves)
│  │  ├─ Search warrants for suspect locations
│  │  ├─ Phone record warrants
│  │  ├─ Financial transaction warrants (if robbery proceeds tracked)
│  │  └─ Court approval process
│  │
│  ├─ Arrest coordination
│  │  ├─ Coordinate timing with field teams
│  │  ├─ Simultaneous arrests (prevent flight/evidence destruction)
│  │  ├─ Post-arrest interrogation coordination
│  │  └─ Miranda rights documentation
│  │
│  ├─ Evidence collection post-arrest
│  │  ├─ Physical evidence from arrests (weapons, cash, etc.)
│  │  ├─ Interrogation statements
│  │  ├─ Digital forensics (phones, computers)
│  │  └─ Forensic analysis (ballistics, DNA, etc.)
│  │
│  └─ Supervisor oversight
│     ├─ Validate arrest legality (rights protection)
│     ├─ Ensure evidence chain of custody
│     └─ Document all procedures
│
├─ PHASE 4: PROSECUTION PREPARATION (Weeks 13+)
│  ├─ Coordinate with prosecutor
│  │  ├─ Present evidence package
│  │  ├─ Discuss charges and strategy
│  │  ├─ Identify prosecution gaps (additional evidence needed?)
│  │  └─ Timeline for filing charges
│  │
│  ├─ Evidence finalization
│  │  ├─ Forensic reports complete
│  │  ├─ Witness statements final
│  │  ├─ Digital evidence packaged
│  │  └─ Chain of custody audited
│  │
│  └─ Case closure
│     ├─ Investigation summary (what was proven about gang operations)
│     ├─ All related FIRs closed (investigations completed)
│     ├─ Prosecutor acknowledges evidence receipt
│     └─ Supervisor final approval
│
└─ POST-INVESTIGATION
   ├─ Monitor gang activity for patterns (ongoing intelligence)
   ├─ Track prosecution progress
   └─ Identify gang intelligence for future operations
```

**Manual Steps:**
- Supervisor decision to link cases into gang investigation
- Informant cultivation and intelligence gathering
- Warrant applications and court submissions
- Arrest coordination with field teams
- Prosecution coordination
- Final closure review

**Automatable Steps:**
- Crime series detection (Phase 7)
- Phase milestones and checkpoint reminders
- Evidence aggregation from multiple cases
- Witness and suspect list generation
- Warrant timeline tracking
- Prosecution readiness validation

**Decision Points:**
- Are cases truly linked? (sufficient MO similarity)
- Are suspects sufficiently identified? (proceed to arrests?)
- Is evidence adequate for prosecution? (prosecutor consultation)
- Should gang structure investigation expand? (more members involved?)

**Failure Points:**
- Suspect flees before arrest (surveillance gaps) → activate statewide alert
- Evidence inadmissible (rights violation) → investigation must exclude that evidence
- Witness recants (intimidation?) → investigate intimidation separately
- Prosecutor declines charges (insufficient evidence) → identify gaps, conduct follow-up investigation

**Audit Requirements:**
- Weekly supervisor checkpoints logged
- Warrant applications and court approvals documented
- Arrest procedures documented (rights protections, proper procedures)
- Chain of custody for all evidence
- Prosecutor coordination documented
- Final outcome (charges filed / evidence insufficient / gang dismantled)

---

## Workflow 5: Supervisor Shift Handover

```
┌─ END OF SHIFT (Supervisor A)
│
├─ HANDOVER PREPARATION (30 min before shift end)
│  ├─ System generates shift summary
│  │  ├─ Cases assigned today: count and list
│  │  ├─ Cases escalated: count and list
│  │  ├─ SLA breaches: count and details
│  │  ├─ Pending approvals: warrant requests, etc.
│  │  ├─ Critical cases: status update needed
│  │  └─ Analyst incidents: absences, conflicts, concerns
│  │
│  ├─ Supervisor A reviews and annotates
│  │  ├─ Summarize major developments
│  │  ├─ Highlight critical items needing immediate attention
│  │  ├─ Flag any blocked cases (waiting for external action)
│  │  ├─ Document any team issues (conflict, overload, etc.)
│  │  └─ Capture any protocol deviations or concerns
│  │
│  └─ System creates handover record
│     └─ Timestamp, Supervisor A signature, handover content
│
├─ HANDOVER COMMUNICATION (10 min before shift end)
│  ├─ Supervisor A briefs Supervisor B (verbal + written handover)
│  │  ├─ Walk through critical cases
│  │  ├─ Highlight escalations
│  │  ├─ Discuss team status
│  │  ├─ Flag any concerns
│  │  └─ Provide context for pending decisions
│  │
│  └─ Supervisor B acknowledges receipt
│     └─ System logs acknowledgement with timestamp
│
├─ SHIFT TRANSITION
│  ├─ Supervisor A off duty
│  ├─ Supervisor B assumes operational command
│  │  ├─ Reviews handover document
│  │  ├─ Assesses operational status
│  │  └─ Identifies any immediate actions needed
│  │
│  └─ New analyst queue
│     └─ Cases arriving during off-shift hours assigned to Supervisor B
│
└─ HANDOVER DOCUMENTATION
   ├─ Handover record stored (audit trail)
   ├─ Both supervisors' signatures required
   └─ Linked to shift entity for historical reference
```

**Manual Steps:**
- Supervisor A synthesis of shift developments
- Verbal handover communication
- Supervisor B shift readiness assessment

**Automatable Steps:**
- Shift summary generation (cases, escalations, breaches)
- Handover reminder 30 min before shift end
- Handover record creation
- Handover acknowledgement workflow

**Decision Points:**
- Are there immediate actions needed before shift end? (warrant approvals, escalations)
- Are any cases at critical juncture? (need extended coverage into night shift?)

**Failure Points:**
- Supervisor B unavailable at shift end (coverage gap) → activate on-call
- Critical case developed during shift end → no handover communication → issue missed
- Handover not documented (no audit trail) → retroactively document

**Audit Requirements:**
- Handover content documented and searchable
- Both supervisor signatures (authentication)
- Timestamp of handover
- Any deviations from standard procedures noted

---

## Workflow 6: SLA Breach & Escalation

```
┌─ CASE ASSIGNED (Investigation starts, SLA timer begins)
│  Example: murder case, SLA = 30 days average investigation
│
├─ MONITORING (continuous)
│  ├─ Day 5: system generates status
│  ├─ Day 15: system generates status
│  ├─ Day 24: ALERT "Case approaching SLA breach (6 days remaining)"
│  │  └─ Supervisor reviews case, assesses on-track status
│  │
│  └─ Day 29: FINAL ALERT "Case breaching SLA tomorrow"
│     └─ Supervisor must take action (extend SLA or breach)
│
├─ IF ON TRACK
│  ├─ Supervisor acknowledges alert
│  ├─ Investigation continues
│  └─ SLA deadline = day 30
│
├─ IF NOT ON TRACK (Day 25+)
│  ├─ Supervisor has options
│  │  ├─ Option A: Request SLA extension
│  │  │  ├─ Supervisor documents reason (awaiting evidence, complex case, etc.)
│  │  │  ├─ Supervisor requests extension (5, 10, or 15 days)
│  │  │  ├─ Approving authority (ACP for extensions > 10 days)
│  │  │  └─ SLA timer resets
│  │  │
│  │  ├─ Option B: Accelerate investigation
│  │  │  ├─ Request additional resources (analysts, teams)
│  │  │  ├─ Prioritize critical evidence
│  │  │  ├─ Compress investigation timeline
│  │  │  └─ Accept higher risk of oversight
│  │  │
│  │  └─ Option C: Restructure investigation
│  │     ├─ Close primary investigation (insufficient evidence)
│  │     ├─ Open "cold case" file
│  │     └─ Mark for periodic review (annual or when new evidence surfaces)
│  │
│  └─ Supervisor documents decision (audit trail)
│
├─ IF SLA BREACHED (Day 30 reached)
│  ├─ Automatic escalation to ACP
│  ├─ Escalation includes
│  │  ├─ Investigation status and timeline
│  │  ├─ Evidence collected so far
│  │  ├─ Outstanding evidence/tasks
│  │  ├─ Supervisor assessment (why delayed?)
│  │  ├─ Resources already allocated
│  │  └─ Recommended path forward
│  │
│  ├─ ACP reviews and decides
│  │  ├─ Approve extension (and allocate additional resources)
│  │  ├─ Convert to cold case (document reason)
│  │  ├─ Escalate to DCP (if SLA critical, e.g., murder)
│  │  └─ Require additional supervisor training (if repeated pattern)
│  │
│  └─ Audit trail records all escalations and decisions
│
└─ POST-RESOLUTION
   ├─ Case closed (day 35, SLA extended 5 days)
   ├─ Investigation outcome documented
   ├─ Root cause analysis (why was extension needed?)
   └─ Escalation and extension permanently logged
```

**Manual Steps:**
- Supervisor assessment at 80% of SLA (on track or not?)
- Supervisor decision (extend/accelerate/close)
- ACP decision on breached SLA

**Automatable Steps:**
- SLA calculation from case assignment
- Alert generation at day 24 and day 29
- Escalation to ACP at day 30 (if not extended)
- Documentation of all escalations

**Decision Points:**
- Is investigation on track? (supervisor judgment)
- Should SLA be extended? (supervisor + ACP approval)
- If not extended, should case close or go cold? (ACP decision)

**Failure Points:**
- Supervisor ignores alert (case breaches SLA undetected) → ACP detects on monthly review
- No justification documented (why was SLA extended?) → retroactively document
- Repeated SLA breaches for same analyst (pattern) → training required

**Audit Requirements:**
- Every alert sent and supervisor acknowledgement
- Every extension request and approval authority
- Every breach and escalation
- Root cause analysis for each breach
- Final outcome and justification

---

## Workflow 7: Approval Workflow (Warrant Request)

```
┌─ ANALYST IDENTIFIES NEED: Warrant required for phone records
│
├─ ANALYST PREPARATION
│  ├─ Documents justification
│  │  ├─ Why warrant is needed
│  │  ├─ What evidence supports probable cause
│  │  ├─ What information warrant will obtain
│  │  └─ How it advances investigation
│  │
│  └─ Drafts warrant request (formal document)
│     ├─ Affidavit describing crime, evidence, chain of reasoning
│     ├─ Specific records/information requested
│     ├─ Timeline (urgency)
│     └─ Proposed scope (narrow vs. broad request)
│
├─ SUPERVISOR REVIEW & APPROVAL
│  ├─ Supervisor reviews warrant request
│  │  ├─ Is probable cause documented?
│  │  ├─ Is request scope appropriate?
│  │  ├─ Is there legal risk?
│  │  ├─ Has analyst interpreted law correctly?
│  │  └─ Is this urgency justified?
│  │
│  ├─ Supervisor decision
│  │  ├─ APPROVE: send to court
│  │  ├─ REVISE: request analyst to narrow/expand scope
│  │  ├─ REJECT: tell analyst warrant not justified
│  │  └─ ESCALATE: pass to ACP for legal review (complex cases)
│  │
│  ├─ If approved: system creates warrant submission task
│  │  ├─ Submit to court (digital filing or in-person)
│  │  ├─ Track approval status
│  │  ├─ Target SLA: approval within 3 days
│  │  └─ Escalate if court doesn't respond
│  │
│  └─ Audit log
│     └─ Supervisor approval, timestamp, any conditions/notes
│
├─ IF SUPERVISOR REQUESTS REVISION
│  ├─ Analyst revises warrant request
│  ├─ Resubmit to supervisor
│  ├─ Supervisor re-reviews
│  └─ Cycle repeats until approved
│
├─ IF SUPERVISOR REJECTS
│  ├─ Analyst must pursue alternative approach
│  ├─ Escalate to ACP if analyst believes supervisor wrong
│  └─ Document reasoning for rejection
│
├─ COURT SUBMISSION & APPROVAL
│  ├─ Once supervisor approves: warrant submitted to court
│  ├─ Court reviews (typically 1-3 days)
│  ├─ Court decision: APPROVE / DENY / REQUEST REVISION
│  │  ├─ APPROVE: warrant valid, analyst proceeds to execute
│  │  ├─ DENY: warrant rejected, analyst must use alternative approach
│  │  └─ REVISION: court requests changes, resubmit
│  │
│  └─ System tracks warrant status → analyst notified when approved
│
└─ WARRANT EXECUTION
   ├─ Analyst uses approved warrant to request records from target
   ├─ Target entity (telecom, bank, etc.) responds
   ├─ Records obtained and linked to investigation
   └─ Chain of custody documented
```

**Manual Steps:**
- Analyst warrant request drafting
- Supervisor review and approval/rejection
- Court submission
- Court decision
- Analyst warrant execution

**Automatable Steps:**
- Warrant submission tracking
- SLA monitoring (3-day court decision target)
- Escalation if court doesn't respond
- Notification to analyst when approved

**Decision Points:**
- Is probable cause sufficient? (supervisor/court judgment)
- Is scope appropriate? (avoid overly broad searches)
- Is urgency justified? (expedited processing?)

**Failure Points:**
- Court denies warrant (probable cause insufficient) → must use alternative approach
- Court requires revision (scope too broad) → resubmit
- Warrant approval delayed beyond SLA → escalate to court, use alternative approach

**Audit Requirements:**
- Supervisor approval documented with justification
- Court approval/denial documented
- Warrant used appropriately (only requested records accessed)
- All results from warrant linked to investigation

---

# DELIVERABLE 3: OPERATIONAL DATA MODEL

## Core Entities

### Entity: Investigation (Enhancement to Phase 2)

**Purpose:**
Central entity representing a criminal investigation with status, ownership, and operational tracking.

**Attributes:**
- `investigation_id` (PK): unique identifier
- `fir_id` (FK): linked FIR (one FIR → one investigation minimum)
- `investigation_type`: enum {CRIMINAL, CIVIL, ADMINISTRATIVE}
- `case_type`: enum {MURDER, ROBBERY, THEFT, CYBER, MISSING_PERSON, GANG, etc.}
- `priority`: enum {CRITICAL, HIGH, MEDIUM, LOW}
- `status`: enum {CREATED, ASSIGNED, ACTIVE, AWAITING_REVIEW, SUSPENDED, CLOSED}
- `assigned_analyst_id` (FK): current primary analyst
- `supervising_supervisor_id` (FK): responsible supervisor
- `parent_investigation_id` (FK): for linked cases (gang investigation parent)
- `created_at`: timestamp
- `assigned_at`: timestamp when assigned to analyst
- `last_activity_at`: last update to investigation
- `closed_at`: timestamp when investigation closed
- `investigation_summary`: text field (final summary)
- `investigation_outcome`: enum {SOLVED, UNSOLVED, FALSE_LEAD, COLD_CASE}
- `evidence_count`: denormalized count of linked evidence items
- `task_count`: denormalized count of open tasks

**Lifecycle:**
1. CREATED - investigation initialized from FIR
2. ASSIGNED - analyst assigned by supervisor
3. ACTIVE - analyst working on investigation
4. AWAITING_REVIEW - analyst requests closure, awaiting supervisor approval
5. SUSPENDED - investigation paused (waiting for external event)
6. CLOSED - supervisor approved closure

**Relationships:**
- Investigation → FIR (N:1)
- Investigation → Analyst (N:1)
- Investigation → Supervisor (N:1)
- Investigation → Task (1:N)
- Investigation → Evidence (1:N)
- Investigation → Investigation (self-referential, parent)

**Retention Policy:**
- Active: maintain indefinitely
- Closed < 5 years: maintain for appeals/review
- Closed > 5 years: archive (queryable but not updated)
- Cold case: maintain indefinitely (annual review)

---

### Entity: Task

**Purpose:**
Discrete action item within an investigation (collect evidence, interview witness, obtain warrant).

**Attributes:**
- `task_id` (PK): unique identifier
- `investigation_id` (FK): parent investigation
- `task_type`: enum {COLLECT_EVIDENCE, INTERVIEW_WITNESS, OBTAIN_WARRANT, CONTACT_AGENCY, FORENSIC_REQUEST, etc.}
- `title`: short description ("Collect blood evidence from scene")
- `description`: detailed requirements
- `assigned_to_id` (FK): analyst responsible
- `supervisor_id` (FK): supervisor overseeing
- `status`: enum {CREATED, ASSIGNED, IN_PROGRESS, AWAITING_INPUT, BLOCKED, COMPLETED, CANCELLED}
- `priority`: enum {CRITICAL, HIGH, MEDIUM, LOW}
- `created_at`: timestamp
- `assigned_at`: timestamp when assigned to analyst
- `completed_at`: timestamp when marked complete
- `due_date`: expected completion date
- `sla_due_date`: hard deadline (SLA)
- `sla_breached_at`: when SLA breached (if applicable)
- `depends_on_task_id` (FK): prerequisite task (for ordering)
- `completion_evidence`: linked evidence or notes proving completion
- `notes`: analyst notes on task execution
- `is_recurring`: boolean (for recurring tasks)
- `recurrence_rule`: cron-like recurrence pattern

**Relationships:**
- Task → Investigation (N:1)
- Task → Analyst (N:1)
- Task → Task (self-referential, depends_on)

**Lifecycle:**
1. CREATED - task generated (from template or supervisor)
2. ASSIGNED - task assigned to analyst
3. IN_PROGRESS - analyst actively working
4. AWAITING_INPUT - task blocked (waiting for external input)
5. BLOCKED - task cannot proceed (predecessor not complete)
6. COMPLETED - analyst marks complete
7. CANCELLED - task no longer needed

---

### Entity: Assignment

**Purpose:**
Track assignment of investigation to analyst, with reasoning and SLA.

**Attributes:**
- `assignment_id` (PK): unique identifier
- `investigation_id` (FK): what was assigned
- `analyst_id` (FK): who it was assigned to
- `supervisor_id` (FK): who made the assignment
- `created_at`: when assignment made
- `reason`: why this analyst selected (skill match, workload, jurisdiction, etc.)
- `system_suggested`: boolean (was this system suggestion or override?)
- `sla_baseline_days`: expected investigation duration (30 days for murder)
- `sla_due_date`: deadline (created_at + sla_baseline_days)
- `status`: enum {ACTIVE, TRANSFERRED, REASSIGNED}
- `notes`: any special considerations

**Relationships:**
- Assignment → Investigation (N:1)
- Assignment → Analyst (N:1)
- Assignment → Supervisor (N:1)

**Retention Policy:**
- Permanent (audit trail)

---

### Entity: SLA

**Purpose:**
Define operational SLAs by case type, track compliance.

**Attributes:**
- `sla_id` (PK): unique identifier
- `case_type`: enum {MURDER, ROBBERY, THEFT, CYBER, MISSING_PERSON, etc.}
- `baseline_days`: expected investigation duration (30 for murder, 14 for robbery)
- `critical_tasks`: tasks that must complete before closure
- `created_by_supervisor_id` (FK): who defined this SLA
- `effective_date`: when this SLA came into effect
- `notes`: rationale for SLA duration

**Relationships:**
- SLA → CaseType (1:1)

**Retention Policy:**
- Permanent (historical record)

---

### Entity: SLAViolation

**Purpose:**
Track SLA breaches for analysis and root cause investigation.

**Attributes:**
- `violation_id` (PK): unique identifier
- `investigation_id` (FK): which investigation breached SLA
- `sla_id` (FK): which SLA was breached
- `sla_due_date`: deadline that was missed
- `breached_at`: actual completion date
- `days_late`: breached_at - sla_due_date
- `reason`: why breached (documented by supervisor)
- `escalated_to_supervisor_id` (FK): supervisor who handled breach
- `escalated_to_acp_id` (FK): ACP who approved extension (if applicable)
- `extension_approved`: boolean
- `extension_days`: additional days granted
- `new_due_date`: revised deadline
- `created_at`: when breach detected

**Relationships:**
- SLAViolation → Investigation (N:1)
- SLAViolation → SLA (N:1)
- SLAViolation → Supervisor (N:1)

**Retention Policy:**
- Permanent (compliance audit trail)

---

### Entity: Notification

**Purpose:**
Track all notifications sent to users (alerts, escalations, approvals needed).

**Attributes:**
- `notification_id` (PK): unique identifier
- `recipient_id` (FK): who the notification is for
- `notification_type`: enum {CASE_ASSIGNED, ESCALATION, APPROVAL_NEEDED, SLA_WARNING, TASK_DUE, SHIFT_HANDOVER, etc.}
- `priority`: enum {CRITICAL, HIGH, MEDIUM, LOW}
- `title`: short message ("New case assigned: K-001")
- `body`: detailed message
- `related_investigation_id` (FK): investigation context
- `related_task_id` (FK): task context
- `created_at`: sent timestamp
- `delivered_at`: when delivered to client
- `read_at`: when recipient read notification
- `acknowledged_at`: when recipient acknowledged (for critical notifications)
- `acknowledged_by`: user who acknowledged
- `action_taken`: did recipient take action? (yes/no/pending)
- `delivery_channel`: enum {IN_APP, EMAIL, SMS, DASHBOARD}
- `delivery_status`: enum {PENDING, DELIVERED, FAILED}

**Relationships:**
- Notification → Officer (N:1)
- Notification → Investigation (N:1, optional)
- Notification → Task (N:1, optional)

**Retention Policy:**
- Keep for 1 year (compliance/audit)
- Archive older notifications

---

### Entity: Escalation

**Purpose:**
Track escalations of cases to higher authority (supervisor → ACP → DCP).

**Attributes:**
- `escalation_id` (PK): unique identifier
- `investigation_id` (FK): what was escalated
- `from_supervisor_id` (FK): who initiated escalation
- `escalated_to_role`: enum {SUPERVISOR, ACP, DCP, COMMISSIONER}
- `escalated_to_id` (FK): specific person
- `reason`: why escalated (SLA breach, legal complexity, inter-agency coordination, etc.)
- `created_at`: when escalated
- `decision_at`: when recipient made decision
- `decision`: enum {APPROVED, REJECTED, NEEDS_CLARIFICATION}
- `decision_notes`: recipient's reasoning
- `status`: enum {PENDING, ESCALATED, RESOLVED}

**Relationships:**
- Escalation → Investigation (N:1)
- Escalation → Supervisor (N:1, from)
- Escalation → Officer (N:1, to)

**Retention Policy:**
- Permanent (audit trail)

---

### Entity: Evidence (Enhancement to Phase 7)

**Purpose:**
Existing Phase 7 entity, enhanced for operational workflow.

**New Attributes (Phase 8):**
- `collection_status`: enum {REQUESTED, RECEIVED, VERIFIED, REJECTED, MISSING}
- `collection_requested_at`: when request made
- `collection_due_date`: when evidence expected to arrive (SLA)
- `collection_received_at`: when actually received
- `verified_at`: when analyst verified correctness
- `verification_notes`: analyst's assessment
- `chain_of_custody_logged`: boolean (complete audit trail)
- `investigation_id` (FK): which investigation(s) this evidence applies to
- `linked_at`: when linked to investigation

**Relationships:**
- Evidence → Investigation (N:N, many-to-many)

---

### Entity: Shift

**Purpose:**
Define supervisor shifts and coverage.

**Attributes:**
- `shift_id` (PK): unique identifier
- `supervisor_id` (FK): which supervisor
- `start_time`: shift start (e.g., 9:00 AM)
- `end_time`: shift end (e.g., 5:00 PM)
- `day_of_week`: enum {MON, TUE, WED, THU, FRI, SAT, SUN}
- `is_on_call`: boolean (on-call shift for after-hours coverage)
- `max_cases_under_management`: integer (how many cases one supervisor can oversee)
- `effective_date`: when shift started
- `end_date`: when shift ended (if changed)

**Relationships:**
- Shift → Supervisor (N:1)

**Retention Policy:**
- Keep for 2 years (operational history)

---

### Entity: ShiftHandover

**Purpose:**
Document supervisor handovers between shifts.

**Attributes:**
- `handover_id` (PK): unique identifier
- `from_shift_id` (FK): shift ending
- `to_shift_id` (FK): shift starting
- `from_supervisor_id` (FK): outgoing supervisor
- `to_supervisor_id` (FK): incoming supervisor
- `handover_summary`: text of shift summary
- `critical_cases`: list of case IDs requiring attention
- `escalations`: any escalations from this shift
- `team_notes`: personnel issues, conflicts, etc.
- `created_at`: handover timestamp
- `acknowledged_at`: incoming supervisor's acknowledgement
- `acknowledged_by`: who acknowledged

**Relationships:**
- ShiftHandover → Shift (N:1, from & to)
- ShiftHandover → Supervisor (N:1, from & to)
- ShiftHandover → Investigation (N:N)

**Retention Policy:**
- Keep for 5 years (operational history, legal holds)

---

### Entity: Officer (Enhancement)

**Purpose:**
Existing Phase 2 entity, enhanced with operational attributes.

**New Attributes (Phase 8):**
- `current_assignment_count`: denormalized count of open investigations
- `max_capacity`: integer (max cases can handle concurrently)
- `skill_tags`: array of strings ["cyber-crime", "missing-persons", "gang-investigation"]
- `certifications`: array with dates ["forensic-photography: 2025-06-15", "undercover: 2024-12-01"]
- `jurisdiction_coverage`: array of district IDs ["DIST-01", "DIST-02"]
- `shift_id` (FK): current shift assignment
- `supervisor_id` (FK): reporting supervisor
- `performance_rating`: numeric (1-5, updated quarterly)
- `escalation_count_this_month`: integer (how many cases escalated)
- `sla_compliance_rate`: percentage (% of SLAs met)
- `operational_status`: enum {ACTIVE, ON_LEAVE, SUSPENDED, RETIRED}

**Relationships:**
- Officer → Shift (N:1)
- Officer → Supervisor (N:1)

---

### Entity: OperationalAlert

**Purpose:**
Real-time alerts for command centre (SLA breaches, escalations, critical cases).

**Attributes:**
- `alert_id` (PK): unique identifier
- `alert_type`: enum {SLA_WARNING, SLA_BREACH, ESCALATION, CASE_ASSIGNED, CRITICAL_CASE}
- `investigation_id` (FK): related investigation
- `priority`: enum {CRITICAL, HIGH, MEDIUM, LOW}
- `message`: alert text
- `created_at`: when generated
- `acknowledged_at`: when supervisor acknowledged
- `acknowledged_by_id` (FK): who acknowledged
- `action_taken`: what action was taken in response

**Relationships:**
- OperationalAlert → Investigation (N:1)

**Retention Policy:**
- Keep for 1 year

---

# DELIVERABLE 4: ROLE ANALYSIS

## Role: Analyst

**Responsibilities:**
- Conduct criminal investigations independently
- Collect and analyze evidence
- Interview witnesses and suspects
- Link cases to crime series (leverage Phase 7)
- Complete investigative tasks on schedule
- Document findings in investigation record
- Request supervisor approval for warrants/actions
- Coordinate with external agencies

**Permissions:**
- Create tasks within own investigation
- Read own investigation and related investigations
- Read intelligence from Phase 7 (crime series, entity connections)
- Edit investigation notes and evidence findings
- Request supervisor approval (cannot approve own actions)
- Access witness/suspect contact information
- Request evidence from collection units

**Daily Workflow:**
1. Start of shift: review own case queue (5-10 active cases)
2. Check notifications: new cases assigned, task reminders, supervisor messages
3. Prioritize work: which tasks due today, which SLAs approaching?
4. Execute tasks: evidence collection, interviews, warrant requests
5. Update investigation status: mark tasks complete, add notes
6. Request approval: warrant requests to supervisor
7. End of shift: update supervisor on progress, flag any issues

**Pain Points:**
- Too many cases (overloaded, quality suffers)
- Blocked tasks (waiting for evidence, warrant approval, external agencies)
- Unclear expectations (what constitutes "complete investigation"?)
- Lack of feedback (don't know if investigation approach is sound)
- Evidence delays (can't proceed without physical evidence)
- Approval bottleneck (supervisor too busy to review warrants quickly)

**Information Required:**
- Case details, FIR information
- Intelligence from Phase 7 (related cases, entities, patterns)
- Task assignments and due dates
- Evidence collection status
- Inter-agency request status
- Supervisor expectations and feedback
- Precedent cases (for guidance on similar investigations)

**KPIs:**
- Average investigation age (target: 21 days, varies by case type)
- SLA compliance (target: 98%)
- Case closure rate (target: 6-8 cases/month)
- Evidence collection rate (target: complete before closure)
- Supervisor approval rate (how many warrant requests approved on first submission)
- Escalation rate (should be low, indicates smooth workflow)

---

## Role: Supervisor

**Responsibilities:**
- Oversee 5-10 analysts and their investigations
- Assign new cases to analysts (balance workload)
- Monitor investigation progress and SLA compliance
- Approve warrants and high-risk actions
- Escalate stalled cases
- Conduct shift handovers
- Provide coaching and feedback to analysts
- Manage inter-agency coordination
- Ensure quality and legal compliance

**Permissions:**
- View all investigations in district
- Assign investigations to analysts
- Approve warrants, arrests, evidence collection
- Create and assign tasks
- Close investigations (final approval)
- View all analyst workload and performance
- Approve SLA extensions
- Escalate to ACP if needed
- Access all intelligence and evidence

**Daily Workflow:**
1. Start of shift: receive handover from previous supervisor
2. Review pending approvals: warrant requests, closure requests
3. Monitor dashboards: SLA compliance, analyst workload, critical cases
4. Assign new cases: assess incoming FIRs, allocate to analysts
5. Oversight activities:
   - Approve warrants (legal review)
   - Review investigation progress
   - Escalate SLA-approaching cases
   - Resolve inter-analyst conflicts
   - Provide guidance on complex cases
6. End of shift: prepare handover for incoming supervisor
7. Weekly: review analyst performance, update performance ratings

**Pain Points:**
- Information overload (100+ cases, many requiring oversight)
- Decision bottleneck (analysts waiting for warrant approvals)
- No visibility into why cases delayed (external agencies, evidence, etc.)
- Inconsistent quality across analysts
- Difficulty balancing workload (overloaded analysts + underutilized analysts)
- No systematic way to track approval decisions
- SLA breaches discovered after breach (reactive rather than proactive)

**Information Required:**
- Real-time case status (which cases need attention?)
- SLA tracking (which cases approaching deadline?)
- Analyst workload distribution
- Pending approvals (warrants, closures)
- Escalations and issues from field
- Intelligence from Phase 7 (to inform case assignments)
- Officer skill/jurisdiction data (to match cases to analysts)
- Performance data per analyst

**KPIs:**
- District SLA compliance (target: 98%)
- Average approval time for warrants (target: < 4 hours)
- Escalation frequency (should be < 5/week)
- Analyst satisfaction (retention, feedback)
- Investigation quality (supervisor-approved closures, appeals)
- Workload balance across team (Gini coefficient < 0.3)

---

## Role: ACP (Assistant Commissioner of Police)

**Responsibilities:**
- Oversee multiple supervisors and districts
- Strategic resource allocation
- Escalation review and approval
- SLA compliance at district level
- Quality assurance reviews
- Inter-district coordination
- Performance management
- Policy development

**Permissions:**
- View all investigations across district
- Approve SLA extensions (> 10 days)
- Escalation review and decision authority
- View all analyst and supervisor performance
- Allocate resources across supervisors
- Close investigations (if supervisor closure reviewed and appealed)
- Access all intelligence and evidence

**Daily Workflow:**
1. Review escalations from supervisors (SLA breaches, complex cases)
2. Monitor district-level KPIs: SLA compliance, resource utilization
3. Resource allocation: move analysts between teams, approve hiring
4. Quality assurance: audit 5-10 closed cases/week for legal compliance
5. Weekly briefing to DCP: district status, escalations, resource needs
6. Handle inter-agency coordination (state-level issues)
7. Performance management: quarterly reviews, coaching

**Pain Points:**
- Limited visibility into day-to-day operations
- Escalations come late (after SLA breach, not before)
- Resource constraints (not enough analysts for workload)
- Inconsistent quality across supervisors
- Political pressure (certain case types require attention)
- No trend analysis (which case types take longest?)

**Information Required:**
- District-level KPIs (aggregated by supervisor, case type)
- Escalation summary (which cases, why, what's the trend?)
- Resource utilization (analysts loaded, underutilized)
- Quality audit results
- Performance trends per supervisor
- Inter-agency status

**KPIs:**
- District SLA compliance (target: 98%)
- Average time to escalation (should be proactive, before breach)
- Resource utilization (target: 85-90%)
- Analyst and supervisor retention
- Quality audit pass rate (target: 95%)
- Inter-agency coordination response time

---

## Role: DCP (Deputy Commissioner of Police)

**Responsibilities:**
- Oversee all ACPs and districts
- State-level strategy and resource allocation
- Political liaison (mayor, state government)
- Major case oversight (murder, terrorism, major crimes)
- Public relations and media coordination
- Budget and staffing decisions
- Policy development
- Oversight of specialized units

**Permissions:**
- View high-level dashboards across all districts
- Escalation review and appeal
- Policy approval authority
- Resource allocation across districts
- Access to all investigations (summary level)

**Daily Workflow:**
1. Morning briefing: state-level status, major escalations
2. Handle political requests (mayor's office, state government)
3. Major case oversight: 1-2 high-profile cases/week
4. Policy decisions: new procedures, resource allocation
5. Budget and staffing: quarterly planning
6. Public relations: media coordination on major cases

**Pain Points:**
- Detached from operational reality (only sees summaries)
- Political pressure on investigation outcomes
- Resource disputes with other state agencies
- Limited visibility into investigative quality
- Crisis management (major incident requiring coordination)

**Information Required:**
- State-level KPIs (by district)
- Major escalations only
- Budget and staffing status
- Political/media issues requiring attention

**KPIs:**
- State-level SLA compliance
- Major case resolution rate
- Political/media satisfaction (as measure of communication)
- Budget vs. actual spending

---

## Role: Command Centre Operator

**Responsibilities:**
- Monitor all operations in real-time
- Dispatch new cases to supervisors
- Route escalations appropriately
- Coordinate with external agencies (911, other districts)
- Track active investigations and incidents
- Alert supervision to emerging issues

**Permissions:**
- View all active cases and incidents
- Create new FIRs in system
- Route cases to supervisors
- Send urgent notifications
- Access emergency contact information

**Daily Workflow:**
1. Monitor incoming cases/FIRs
2. Preliminary triage (priority, type, jurisdiction)
3. Route to appropriate supervisor
4. Track active investigations on master board
5. Handle urgent calls/escalations
6. Coordinate with external agencies

**Pain Points:**
- No visibility into case status (can't tell caller when case will be solved)
- Unclear routing (which supervisor for which case type?)
- Missing critical information (caller details, FIR data)
- Escalation decisions unclear (who to notify?)

**Information Required:**
- Real-time case status
- Supervisor availability and capacity
- Case routing guidelines
- Escalation procedures
- External agency contact information

**KPIs:**
- Time from FIR creation to analyst assignment (target: < 2 hours)
- Routing accuracy (% of cases routed to correct supervisor)
- Escalation response time

---

## Role: Administrator

**Responsibilities:**
- System configuration and maintenance
- User management (create/delete accounts, permissions)
- Data integrity and backups
- Performance monitoring
- Policy enforcement (audit rules, retention)
- Integration with external systems

**Permissions:**
- Full system access
- Create/delete user accounts
- Modify permissions
- Archive/purge data
- System configuration
- Audit all logs

**Daily Workflow:**
1. Monitor system health (performance, uptime)
2. Handle access requests (new users, permission changes)
3. Backups and disaster recovery
4. System updates and patches
5. Compliance checks (data retention, audit logs)

**KPIs:**
- System uptime (target: 99.9%)
- Access request response time (target: < 4 hours)
- Backup success rate (target: 100%)
- Security audit findings (target: 0)

---

## Role: Read-Only Analyst

**Responsibilities:**
- Review investigations for legal/quality purposes
- Prepare case files for prosecution
- Conduct quality audits
- Provide legal counsel

**Permissions:**
- Read all investigations and evidence
- Read audit logs
- No write permissions (cannot modify cases)
- Cannot approve actions

**Daily Workflow:**
1. Review assigned cases for legal readiness
2. Identify missing evidence or procedural issues
3. Prepare case file summaries for prosecution
4. Quality audits per ACP request

**KPIs:**
- Case file quality (% approved for prosecution on first submission)
- Legal issue identification rate

---

# DELIVERABLE 5: SUPERVISOR COMMAND CENTRE

## Operational Dashboard Design

**Purpose:**
Single-pane-of-glass for supervisor to manage 5-10 analysts and 100+ active investigations.

**Design Principles:**
1. **Hierarchical by risk**: CRITICAL cases and alerts at top, oldest/stalled cases visible
2. **Real-time not historical**: focus on NOW, not aggregated metrics
3. **Actionable not informational**: every widget should enable a decision or action
4. **Interrupt-driven alerts**: CRITICAL items demand attention
5. **Workload visibility**: prevent analyst overload

---

## Dashboard Panels

### Panel 1: Critical Alerts (Top, High Priority)

**Content:**
- **SLA Breaches This Hour**: list any investigations that have exceeded SLA deadline
  - Case ID, case type, analyst, days late, current status
  - Action buttons: EXTEND_SLA (with reason), ESCALATE_TO_ACP, CLOSE_INVESTIGATION
  
- **Pending Approvals**: warrants, closures awaiting supervisor decision
  - Request type (warrant/closure), case ID, analyst, time pending
  - Action buttons: APPROVE, REQUEST_REVISION, REJECT
  
- **Critical Cases**: CRITICAL priority cases (kidnapping < 72hrs, terrorism, murder)
  - Case ID, case type, analyst, age, latest activity
  - Action button: DETAIL VIEW
  
- **Analyst Incidents**: off-duty analyst, conflict, escalation
  - Type, details, impact on cases
  - Action button: REASSIGN_CASES (if analyst unavailable)

**Update Frequency:** Real-time (WebSocket push)

**User Action:** "I see 1 SLA breach - let me extend it" → system shows extension form

---

### Panel 2: Analyst Workload Distribution (Left Sidebar)

**Content:**
- For each analyst under supervision:
  - Name, current case count (e.g., "7/10"), workload bar (green if < 8, red if > 10)
  - Cases assigned today (count)
  - Latest activity (time)
  - Status icon: ONLINE, IDLE, OFFLINE, ON_LEAVE
  
**Purpose:** Quick view of team capacity. Identify overloaded analysts.

**User Action:** "Analyst A is at 12 cases - let me reassign 2 to Analyst B"

---

### Panel 3: Case Queue by Status (Center, Main View)

**Content:**
Sortable/filterable list of active cases under supervision:

- **By Status Tabs:**
  - ACTIVE (analyst working)
  - AWAITING_REVIEW (analyst finished, supervisor review pending)
  - AWAITING_INPUT (waiting for external input: evidence, warrant, inter-agency)
  - ESCALATED (awaiting ACP decision)
  - SUSPENDED (on hold)

- **For Each Case:**
  - Case ID, case type (icon), priority (CRITICAL/HIGH/MEDIUM/LOW)
  - Analyst assigned
  - Age (days since assignment, color-coded: green < 50%, yellow 50-80%, red > 80% of SLA)
  - Latest activity (timestamp)
  - Task count (open/total)
  - Evidence count (collected/required)

- **Sorting Options:**
  - By age (oldest first)
  - By SLA remaining (deadline soonest first)
  - By activity (stale cases first)

**User Actions:**
- Click case → detail view (investigation summary, tasks, evidence)
- "REASSIGN" → change analyst
- "EXTEND_SLA" → request extension
- "CLOSE_INVESTIGATION" → start closure review

---

### Panel 4: SLA Health (Right Sidebar)

**Content:**
- **District SLA Compliance Today**: percentage (target 98%)
  - Breakdown by case type (murder: 95%, robbery: 98%, theft: 99%)
  
- **SLA Violations This Week**: count and trend
  - If up-trend (more violations this week than last): alert icon
  
- **Average Investigation Age**: by case type (e.g., murder 18 days, robbery 12 days)
  - Color-coded against SLA baseline (green = under target, red = over)

- **Escalations This Week**: count and trend

**Purpose:** Quick health check. Spot trends before they become crises.

**User Action:** "Murder cases are slow this week (23 days avg) - probably the backlog from weekend"

---

### Panel 5: Shift Handover (Corner, Shift-Change Only)

**Content (Visible 30 min before shift end):**
- Cases changed status since shift start (new assignments, closures, escalations)
- Critical cases for incoming supervisor's attention
- Pending items (approvals, escalations awaiting decision)

**Action Buttons:**
- "PREPARE_HANDOVER" → drafts summary for incoming supervisor
- "COMPLETE_SHIFT" → archives shift, transfers ownership to incoming supervisor

**Purpose:** Systematic handover between shifts (no lost context).

**User Action:** "My shift ends at 5pm. Let me prepare handover for incoming supervisor."

---

### Panel 6: Intelligence Feed (Bottom, Optional)

**Content:**
- Real-time linkages from Phase 7 intelligence engine
  - "Vehicle V-123 appears in 2 additional cases" → drill down to linked cases
  - "Crime series detected: 5 robberies, same MO" → link to new gang investigation
  - "Suspect S-001 linked to 3 other gang members" → intelligence update

**Purpose:** Analysts miss crime series; Phase 7 catches them and alerts supervisor.

**User Action:** "Oh! These 5 robberies are the same gang. Let me create gang investigation and merge cases."

---

## Dashboard Interactions (Key Workflows)

### Workflow A: Assign New Case

**Supervisor sees:** New case in queue, awaiting assignment

**Supervisor action:**
1. Click "ASSIGN" on case
2. System suggests analyst based on: workload (< 8 cases), skill match, jurisdiction
3. Supervisor can override suggestion (pick different analyst)
4. Click "CONFIRM" → case assigned, analyst notified

**System action:**
- Investigation created, linked to FIR
- Task list auto-generated from case-type template
- Analyst receives notification
- Case moves to "ACTIVE" tab

**Time:** < 30 seconds

---

### Workflow B: Approve Warrant

**Supervisor sees:** Case in "AWAITING_REVIEW" tab with "Warrant Approval Pending"

**Supervisor action:**
1. Click case → detail view
2. Review warrant request (affidavit, justification, scope)
3. Supervisor decision: APPROVE / REQUEST_REVISION / REJECT
4. If APPROVE → warrant submitted to court, analyst notified
5. If REQUEST_REVISION → message analyst, request returns to "AWAITING_INPUT"

**System action:**
- Warrant submission tracked (court approval status monitored)
- Analyst notified of approval/request
- SLA for warrant court approval: 3 days

**Time:** 5-10 minutes per warrant

---

### Workflow C: Escalate SLA-Approaching Case

**Supervisor sees:** Case in ACTIVE tab, age at 90% of SLA (27 days for 30-day SLA)

**System alert:** "⚠️ SLA breach in 3 days: K-001 (murder, analyst A)"

**Supervisor action:**
1. Click case → detail view
2. Assess: is investigation on-track or stuck?
3. If stuck: ESCALATE_TO_ACP (system generates escalation summary)
4. If on-track: EXTEND_SLA (document reason, request goes to ACP for approval)

**System action:**
- Escalation sent to ACP with investigation context
- Analyst notified of escalation (may receive ACP follow-up questions)
- SLA extension request tracked (pending ACP approval)

**Time:** 2-5 minutes per escalation

---

### Workflow D: Shift Handover

**Incoming supervisor sees:** Handover panel 30 min before shift end

**Supervisor action:**
1. Review handover prepared by outgoing supervisor
2. Acknowledge receipt ("RECEIVED" button)
3. System highlights critical cases for attention
4. Outgoing supervisor now offline

**System action:**
- Handover logged (audit trail)
- Case assignments transferred to incoming supervisor
- Incoming supervisor becomes operational manager
- Cases continue investigation seamlessly

**Time:** 5-10 minutes handover

---

# DELIVERABLE 6: TASK MANAGEMENT ARCHITECTURE

## Task Engine Design

**Purpose:**
Enable systematic decomposition of investigations into discrete, trackable tasks.

---

## Task Lifecycle

```
1. CREATED
   - Task generated (from template or supervisor)
   - Assigned to analyst (or unassigned)
   - Status transitions to ASSIGNED
   
2. ASSIGNED
   - Task waiting in analyst's queue
   - Analyst reviews, understands requirements
   - Analyst changes status to IN_PROGRESS
   
3. IN_PROGRESS
   - Analyst actively working on task
   - Updates progress in task notes
   - Can transition to:
     a) COMPLETED (if done)
     b) BLOCKED (if waiting for external input)
     c) AWAITING_INPUT (if requires info from others)
   
4. AWAITING_INPUT
   - Task paused (waiting for evidence, approval, external agency response)
   - Task shows blocker (what's required to proceed?)
   - Supervisor monitors and escalates if SLA breached
   - When blocker resolved: analyst resumes (IN_PROGRESS)
   
5. BLOCKED
   - Task cannot proceed (prerequisite task not complete)
   - Task shows dependency (which task must complete first?)
   - When dependency satisfied: task automatically transitions to ASSIGNED (ready to start)
   
6. COMPLETED
   - Analyst marks complete with evidence (attached file, note, etc.)
   - Supervisor reviews (if required by task type)
   - If supervisor approves: status remains COMPLETED
   - If supervisor requests revision: status reverts to IN_PROGRESS
   
7. CANCELLED
   - Task no longer needed (investigation direction changed, case closed, etc.)
   - Supervisor or analyst can cancel
   - Document reason for cancellation (audit trail)
```

---

## Task Types & Templates

Each case type has a predefined task template that auto-generates when investigation created.

### Template: Murder Investigation

Tasks (in order):

1. **Secure Crime Scene** (prerequisite for all others)
   - Type: ADMINISTRATIVE
   - Description: Ensure crime scene is secured and preserved
   - Due: same day as FIR
   - Depends on: none
   - Evidence: scene photos, security log

2. **Collect Physical Evidence** (multiple tasks, depend on #1)
   - Type: EVIDENCE_COLLECTION
   - Description: Collect blood, DNA, fibers, ballistics from scene
   - Due: 5 days from assignment
   - Depends on: #1 (Secure Crime Scene)
   - External input: forensic lab processing
   - Evidence: lab receipt, evidence inventory

3. **Perform Autopsy** (external, depends on #1)
   - Type: EXTERNAL_COORDINATION
   - Description: Coordinate autopsy with medical examiner
   - Due: 5 days from assignment
   - Depends on: #1 (Secure Crime Scene)
   - External input: medical examiner availability
   - Evidence: autopsy report

4. **Interview Witnesses** (multiple, independent of #2/#3)
   - Type: INTERVIEW
   - Description: Conduct interviews with witnesses present at scene or who saw suspect
   - Due: 3 days (witnesses' memories fade)
   - Depends on: none
   - Evidence: witness statements, recording

5. **Interview Immediate Family** (depends on #3, autopsy results)
   - Type: INTERVIEW
   - Description: Notify family, conduct interview about victim's activities/associates
   - Due: 2 days (family cooperation critical)
   - Depends on: #3 (Autopsy complete, need results to discuss)
   - Evidence: family statement

6. **Obtain Warrant for Suspect Phone Records** (depends on #4, witness identifications)
   - Type: WARRANT
   - Description: Prepare warrant application for phone records of identified suspect
   - Due: 3 days (time-critical for call records)
   - Depends on: #4 (Witness identifications needed for warrant justification)
   - Supervisor approval: required
   - Evidence: warrant copy, court approval

7. **Collect Phone Records** (depends on #6, warrant approved)
   - Type: EXTERNAL_COORDINATION
   - Description: Request phone records from carrier, validate timeline
   - Due: 10 days (external SLA)
   - Depends on: #6 (Warrant approval required)
   - Evidence: carrier response, call log analysis

8. **Obtain Video Footage** (depends on #1, crime scene secured)
   - Type: EXTERNAL_COORDINATION
   - Description: Retrieve CCTV footage from scene and surrounding areas
   - Due: 7 days
   - Depends on: #1 (Scene location needed)
   - Evidence: footage files, location list

9. **Analyze Video Footage** (depends on #8, footage obtained)
   - Type: ANALYSIS
   - Description: Review footage, identify suspect, timeline of movements
   - Due: 5 days after footage received
   - Depends on: #8 (Footage required)
   - Evidence: timeline, suspect identification

10. **Ballistics Analysis** (external, depends on #2)
    - Type: EXTERNAL_COORDINATION
    - Description: Submit projectiles to forensic lab for analysis
    - Due: 10 days
    - Depends on: #2 (Physical evidence)
    - Evidence: ballistics report

11. **DNA Analysis** (external, depends on #2)
    - Type: EXTERNAL_COORDINATION
    - Description: Submit DNA samples to forensic lab for analysis
    - Due: 20 days (longer turnaround)
    - Depends on: #2 (Physical evidence)
    - Evidence: DNA report

12. **Identify Suspect** (depends on #4, #5, #8, #10)
    - Type: ANALYSIS
    - Description: Synthesize all evidence to identify primary suspect
    - Due: 15 days from assignment
    - Depends on: witness descriptions, video, ballistics (all required)
    - Evidence: suspect identification summary

13. **Arrest & Interrogation** (depends on #12, suspect identified)
    - Type: FIELD_OPERATION
    - Description: Coordinate arrest with field team, conduct interrogation
    - Due: 3 days (time-critical before suspect disappears)
    - Depends on: #12 (Suspect identification required)
    - Supervisor approval: required for arrest
    - Evidence: arrest report, interrogation recording

14. **Prepare Prosecution Case** (depends on all above)
    - Type: ANALYSIS
    - Description: Synthesize all evidence into prosecution-ready case file
    - Due: 5 days before SLA deadline
    - Depends on: all other tasks (comprehensive evidence required)
    - Supervisor approval: required before closure
    - Evidence: case summary, evidence checklist

---

## Task Assignment Strategy

### Auto-Assignment (System)

When task created, system can auto-assign based on task type:

- **EVIDENCE_COLLECTION**: Assign to analyst who has evidence expertise
- **INTERVIEW**: Assign to analyst with interview skills, native language match if possible
- **WARRANT**: No auto-assign, requires supervisor decision
- **EXTERNAL_COORDINATION**: Assign to analyst with best relationship with that external entity
- **ANALYSIS**: Assign to analyst with domain expertise (DNA analysis specialist, etc.)

### Manual Assignment (Supervisor)

Supervisor can override auto-assignment:
- Change analyst (if task-specific specialist available, or to balance workload)
- Reassign task between analysts
- Split task (multiple analysts handling parts)

---

## Task Dependencies

### Dependency Types

1. **Hard Dependency (blocks start)**
   - Task B cannot start until Task A complete
   - Example: "Analyze Video Footage" depends on "Collect Video Footage"
   - System enforces: Task B stays BLOCKED until Task A marked COMPLETED

2. **Soft Dependency (informs priority)**
   - Task B should wait for Task A, but can start before completion
   - Example: "Arrest & Interrogation" should wait for "Identify Suspect", but can run in parallel
   - System suggests order but doesn't enforce

### Dependency Validation

System prevents circular dependencies:
- Task A depends on Task B, Task B depends on Task A → system rejects

System detects long chains:
- Task A → B → C → D → E (5 tasks deep) → supervisor alert (investigation too sequential?)

---

## Task Recurring Capability

### Recurring Task Example: Status Check-In

**Template:**
- Task: "Analyst Status Check-In (Supervisor)"
- Supervisor creates as RECURRING
- Recurrence: every 3 days
- System auto-creates new instance: day 0, day 3, day 6, day 9, etc.
- Each instance: supervisor reviews investigation progress, analyst provides update

**System Behavior:**
- On day 0: create first task, assign to analyst
- Analyst completes (provides status update in notes)
- On day 3: automatically create next recurring task
- Continues until investigation closed or recurrence cancelled

### Another Example: Weekly Evidence Status

**Template:**
- Task: "Weekly Evidence Status Report"
- Recurrence: every Monday
- Supervisor checks: which evidence items still outstanding? Any SLA violations?

---

## Task SLA & Escalation

### Task-Level SLA

Each task can have its own SLA (in addition to investigation-level SLA):

- Task: "Collect Physical Evidence" → SLA 5 days
- Task: "Ballistics Analysis" → SLA 10 days (external SLA)
- Task: "Arrest Coordination" → SLA 3 days

### Escalation Workflow

If task approaching SLA:
1. Day before SLA: analyst gets notification ("Task due tomorrow")
2. At SLA deadline: task escalates to supervisor
3. Supervisor can:
   - Extend SLA (if waiting for external input)
   - Reassign (if analyst blocked)
   - Mark as BLOCKED (if waiting for blocker resolution)
   - Cancel (if no longer needed)

---

## Task Completion Verification

### Evidence-Based Completion

Analyst marks task complete by providing evidence:

- Task: "Collect Physical Evidence" → upload evidence inventory
- Task: "Interview Witness" → upload witness statement
- Task: "Obtain Warrant" → upload court approval document

### Supervisor Verification (Optional)

For critical tasks, supervisor must verify completion:

- **Requires Verification:** warrants, arrests, prosecution prep
- **Auto-Approved:** interviews, evidence collection (unless supervisor requests review)

---

# DELIVERABLE 7: NOTIFICATION ARCHITECTURE

## Notification Strategy

**Purpose:**
Deliver time-critical information to users without overwhelming them (manage notification fatigue).

---

## Notification Types & Channels

### CRITICAL Notifications (In-App + Email + SMS)

**Immediate** delivery required (< 5 minutes):

1. **New Case Assigned**
   - "Murder case K-001 assigned to you"
   - Analyst: in-app alert + email + SMS (if configured)
   - Supervisor: in-app alert + email (optional SMS)

2. **SLA Breach Alert**
   - "Case K-001 has breached SLA (30 days) - URGENT"
   - Supervisor: in-app alert + email + SMS
   - ACP: in-app alert + email
   - Analyst: in-app alert

3. **Escalation**
   - "Case K-001 escalated to ACP - requires attention"
   - All involved parties notified

4. **Warrant Approved** (waiting analyst action)
   - "Your warrant for case K-001 has been approved by court"
   - Analyst: in-app alert + email

5. **Critical Case Assigned** (kidnapping < 72 hrs, terrorism)
   - "CRITICAL: Kidnapping case K-001 - 72-hour response required"
   - Supervisor: in-app + email + SMS
   - Analyst: in-app + email + SMS

### HIGH Notifications (In-App + Email)

**Within 30 minutes:**

1. **Task Due Soon**
   - "Task 'Collect Evidence' in case K-001 due tomorrow"
   - Analyst: in-app + email

2. **Evidence Arrived**
   - "Physical evidence collected for case K-001 is ready"
   - Analyst: in-app + email

3. **Supervisor Review Needed**
   - "Case K-001 awaiting your closure review"
   - Supervisor: in-app + email

4. **Inter-Agency Response**
   - "Phone records for case K-001 received from carrier"
   - Analyst: in-app + email

### MEDIUM Notifications (In-App only)

**Within 1 hour:**

1. **Investigation Updated**
   - "Analyst A added findings to case K-001"
   - Supervisor: in-app

2. **Task Completed**
   - "Interview task in K-001 completed by Analyst A"
   - Supervisor: in-app

3. **Status Change**
   - "Case K-001 changed from ACTIVE to AWAITING_REVIEW"
   - Supervisor: in-app

### LOW Notifications (In-App digest)

**Once daily (morning briefing):**

1. **Daily Summary**
   - "4 cases closed yesterday, 2 SLA extensions requested, 12 cases awaiting action"
   - Supervisor: in-app (digest)

2. **Weekly Trends**
   - "SLA compliance this week: 94% (down from 97%)"
   - Supervisor: in-app (weekly)

---

## User Notification Preferences

Each user can configure:

- **Notification Channel Preferences:**
  - In-app: always enabled (no opt-out)
  - Email: enabled/disabled per notification type
  - SMS: enabled/disabled per notification type (for CRITICAL only)

- **Quiet Hours:**
  - Do-not-disturb 6pm-8am (SMS/email suppressed, in-app only)
  - No SMS notifications after 8pm

- **Escalation Preferences:**
  - Auto-escalate to SMS if in-app unread > 2 hours (for CRITICAL only)

---

## Notification Delivery Guarantees

### At-Least-Once Delivery

System must guarantee notification delivered:

1. Generate notification, store in queue
2. Attempt delivery (in-app, email, SMS)
3. If delivery fails: retry with exponential backoff (1s, 5s, 30s, 5m, 30m)
4. Mark delivered after successful send

### Acknowledgement Requirement (CRITICAL only)

For CRITICAL notifications, system requires acknowledgement:

1. Notification sent
2. System tracks: sent_at, read_at, acknowledged_at
3. If not acknowledged within 30 minutes:
   - Auto-escalate to next level (analyst → supervisor → ACP)
   - Send reminder notification

### Delivery Status Tracking

Every notification has delivery status:
- PENDING: not yet delivered
- DELIVERED: successfully sent
- READ: user opened notification
- ACKNOWLEDGED: user explicitly acknowledged (for CRITICAL)
- FAILED: delivery failed after retries

---

## Notification Fatigue Prevention

### Deduplication

If same notification (e.g., "Case K-001 SLA breach") sent multiple times:
- Check if previous notification already sent within 1 hour
- If yes, don't send duplicate, increment counter ("3 new alerts")
- If no, send new notification

### Throttling

Limit notifications to analyst:
- Max 10 notifications per hour (MEDIUM/LOW combined)
- If throttled: aggregate into digest ("7 more tasks completed")

### Digest Aggregation

Instead of individual notifications, batch lower-priority items:
- Task Completed → digest
- Investigation Updated → digest
- Status Changed → digest

---

## Notification Content

### CRITICAL Notification Example

**Title:** "⚠️ URGENT: Case K-001 SLA Breached"

**Body:**
```
Case: K-001 (Murder)
Analyst: Ravi Kumar
SLA Deadline: 2026-07-20
Days Late: 1 day
Status: ACTIVE (investigation ongoing)
Latest Activity: 2026-07-19 14:30 (evidence collection)

Action Required:
- Extend SLA (document reason)
- Escalate to ACP
- Reassign to different analyst

View Full Case →
```

**Channels:** In-app (red background), Email (urgent flag), SMS (alert tone)

---

## Notification Lifecycle

```
1. CREATED
   - Notification generated (event triggered)
   - Stored in queue
   - Assigned priority level
   
2. DELIVERED
   - Delivery channel handles send (in-app, email, SMS)
   - Marked delivered_at
   
3. READ
   - User opens notification in UI (in-app)
   - Marked read_at
   
4. ACKNOWLEDGED
   - User explicitly acknowledges (for CRITICAL)
   - Marked acknowledged_at
   - Satisfies acknowledgement requirement (auto-escalation cancelled)
   
5. ARCHIVED
   - Auto-archive after 7 days (in-app history)
   - User can manually archive earlier
   
6. DELETED
   - After 30 days: permanent deletion
   - Audit trail remains
```

---

# DELIVERABLE 8: OPERATIONAL METRICS & KPIs

## Investigation-Level KPIs

### Investigation Age

**Definition:** Days from assignment to closure (or current age if open)

**Target:** By case type
- Murder: 30 days average
- Robbery: 20 days average
- Missing Person (< 72 hrs): 3 days average
- Theft: 15 days average
- Cyber Fraud: 25 days average

**Calculation:** (closed_date - assigned_date) in days, or (now - assigned_date) for open

**Visualization:** Time series per analyst, boxplot by case type

**Alerting:** If case age > SLA_baseline + 20%, escalate

---

### SLA Compliance

**Definition:** % of cases closed before SLA deadline

**Target:** 98%

**Calculation:** (cases_closed_on_time / total_cases_closed) × 100

**Granularity:**
- Overall (all cases)
- By supervisor
- By analyst
- By case type
- By week/month

**Visualization:** Line chart trending compliance over time, red zone < 95%

**Alerting:** If weekly compliance < 95%, flag to ACP

---

### Evidence Completion Rate

**Definition:** % of critical evidence collected before case closure

**Target:** 95% (some cases close with minor evidence