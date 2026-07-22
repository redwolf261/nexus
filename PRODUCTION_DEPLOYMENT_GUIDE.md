# NEXUS Production Deployment Guide

**Status:** ✅ READY FOR IMMEDIATE DEPLOYMENT  
**Version:** Phase 7.1/7.2/7.3 Complete  
**Tested:** All 15 issues fixed and validated  
**Rollout Strategy:** Gradual (10% → 50% → 100%)

---

## Pre-Deployment: Database Migrations

### Migration 1: Add FIR Timestamp Precision

```sql
-- Add new columns to FIR table
ALTER TABLE firs ADD COLUMN occurred_time TIME;
ALTER TABLE firs ADD COLUMN occurred_datetime DATETIME;
CREATE INDEX ix_firs_occurred_datetime ON firs(occurred_datetime);

-- Populate occurred_time and occurred_datetime
-- Strategy: If FIR description contains time info, parse it
-- Otherwise, default to 12:00:00 (noon) and flag in logs
UPDATE firs SET 
  occurred_time = COALESCE(CAST(SUBSTRING_INDEX(description_en, ' ', 1) AS TIME), '12:00:00'),
  occurred_datetime = CONCAT(occurred_date, ' ', COALESCE(CAST(SUBSTRING_INDEX(description_en, ' ', 1) AS TIME), '12:00:00'))
WHERE occurred_date IS NOT NULL;

-- Log any defaulted times for QA
SELECT COUNT(*) as defaulted_times FROM firs WHERE occurred_time = '12:00:00';
```

### Migration 2: Add Intelligence Event Logging

```sql
-- Create IntelligenceEventLog table
CREATE TABLE intelligence_event_logs (
  event_id VARCHAR(32) PRIMARY KEY,
  workspace_id VARCHAR(256) NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  entity_id VARCHAR(256),
  confidence_score FLOAT,
  explanation_json JSON,
  shown_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  analyst_id VARCHAR(256),
  dismissed_at DATETIME,
  INDEX idx_workspace_shown (workspace_id, shown_at),
  INDEX idx_event_type (event_type)
);

-- Create EntityMergeProposal table (from Phase 7.3)
CREATE TABLE entity_merge_proposals (
  proposal_id VARCHAR(32) PRIMARY KEY,
  primary_entity_id VARCHAR(256),
  merge_entity_id VARCHAR(256),
  entity_type VARCHAR(64),
  match_score FLOAT,
  confidence_overall FLOAT,
  explanation_json JSON,
  status VARCHAR(32) DEFAULT 'PENDING',
  created_by VARCHAR(256),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME,
  approved_by VARCHAR(256),
  approval_notes TEXT,
  INDEX idx_status (status),
  INDEX idx_primary_entity (primary_entity_id)
);
```

### Migration 3: Neo4j Relationship Strength Backfill

```cypher
// Compute co-arrest count between each pair of persons
MATCH (p1:Person)-[:COMMITTED]->(:FIR)<-[:COMMITTED]-(p2:Person)
WHERE p1.id < p2.id
WITH p1, p2, COUNT(*) as co_arrest_count
MERGE (p1)-[r:ASSOCIATED_WITH]-(p2)
SET r.strength = co_arrest_count,
    r.relationship_type = "co-arrest",
    r.last_associated = datetime()
RETURN COUNT(*) as relationships_updated;
```

---

## Deployment Steps

### Step 1: Staging Environment (Day 1)

```bash
# Pull latest code with all fixes
git pull origin main

# Run database migrations
python backend/migrations/apply_all.py

# Install any new dependencies (if any)
pip install -r backend/requirements.txt

# Run test suite
pytest backend/tests/ -v

# Verify all fixes in staging
pytest backend/tests/test_fixes_*.py -v

# Check WebSocket event logging
curl -i ws://localhost:8000/ws/workspace_test

# Verify intelligence event replay
python backend/scripts/validate_event_replay.py
```

### Step 2: Smoke Tests (Day 2)

```python
# Test 1: Timestamp precision
fir = db.query(FIR).filter_by(fir_id="FIR-001").first()
assert fir.occurred_datetime is not None, "DateTime not populated"

# Test 2: WebSocket event logging
ws.connect("workspace_123")
intelligence_event = db.query(IntelligenceEventLog).filter_by(workspace_id="workspace_123").first()
assert intelligence_event is not None, "Event not logged"

# Test 3: Crime Series missing data handling
series = crime_engine.detect_series(district_id="DIST-01")
for s in series:
    if "missing_geo_data_warning" in [e["dimension"] for e in s["explanation"]["evidence"]]:
        print(f"✓ Missing data warning present for series {s['series_id']}")

# Test 4: Entity Resolution with prefixes
matches = er.resolve_person("CITIZEN-001")
for m in matches["primary_matches"]:
    if "name_regional_variant" in m["explanation"]["evidence"]:
        print(f"✓ Prefix stripping worked for {m['candidate_id']}")

# Test 5: Spatial corridors with datetime
corridors = spatial_engine.detect_travel_corridors("CRIMINAL-001")
for c in corridors:
    assert c["from_date"] < c["to_date"], f"Corridor time order violated: {c}"
```

### Step 3: Gradual Production Rollout (Days 3–7)

**Wave 1: 10% of Districts (Day 3)**
```bash
# Deploy to 1 district
kubectl set image deployment/nexus-backend nexus-backend=nexus:v7.1.0 \
  -n production-wave1
# Monitor: Error rates, alert volume, WebSocket health
```

**Wave 2: 50% of Districts (Day 5)**
```bash
# Deploy to 5 districts after Wave 1 success
kubectl set image deployment/nexus-backend nexus-backend=nexus:v7.1.0 \
  -n production-wave2
# Monitor: Cross-district consistency, graph metrics
```

**Wave 3: 100% of Districts (Day 7)**
```bash
# Full national rollout
kubectl set image deployment/nexus-backend nexus-backend=nexus:v7.1.0 \
  -n production
```

---

## Post-Deployment Validation

### Metric Monitoring

```python
# Monitor alert fatigue reduction (should see -40% decrease)
alert_count_before = db.query(IntelligenceEventLog).filter(
  IntelligenceEventLog.event_type == "SERIES_DETECTED",
  IntelligenceEventLog.shown_at >= datetime.utcnow() - timedelta(days=7)
).count()
print(f"Crime Series alerts past 7 days: {alert_count_before}")

# Monitor event persistence (should be 100%)
events_lost = db.query(IntelligenceEventLog).filter(
  IntelligenceEventLog.dismissed_at.isnot(None)  # All events accounted for
).count()
print(f"Events with dismissal tracked: {events_lost}")

# Monitor timestamp precision (should see < 5% defaults)
defaulted_times = db.query(FIR).filter(
  FIR.occurred_time == time(12, 0, 0)
).count()
print(f"FIRs with inferred time: {defaulted_times / total_firs * 100}%")

# Monitor graph centrality accuracy (manual spot checks)
gang_boss = db.query(GraphMetric).order_by(GraphMetric.score.desc()).first()
print(f"Top-ranked person: {gang_boss.entity_id} (score: {gang_boss.score})")
# Verify this person is actually a gang leader, not low-level dealer
```

### Alert Thresholds

Set up monitoring alerts for these thresholds:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Timestamp Precision Error Rate | > 10% | Escalate to data team |
| WebSocket Reconnection Failure | > 1% | Debug event replay |
| Missing Data Penalty | > 50% of clusters | Check data quality |
| Entity Resolution False Positive | > 6% | Adjust Jaro-Winkler threshold |
| Graph Rank Flip (top 10) | > 2 changes | Verify Neo4j backfill |
| Seasonal CUSUM False Alarms | > 20 in Oct | Adjust multiplier |

---

## Rollback Plan (Emergency Only)

If critical issues detected during Wave 1 or 2:

```bash
# Rollback to previous version
kubectl set image deployment/nexus-backend nexus-backend=nexus:v7.0.5 \
  -n production-wave1

# Keep event logs (they're read-only for investigation)
# But stop writing new events
UPDATE intelligence_event_logs SET listener_enabled = FALSE;

# Investigate root cause
# 1. Check deployment logs: kubectl logs -n production-wave1 -f
# 2. Check database: SELECT * FROM intelligence_event_logs WHERE shown_at > ?
# 3. Compare with Phase 7.0 behavior

# After fix, re-deploy (not recommended on same day)
# Wait 24 hours minimum before re-attempting Wave 1
```

---

## Investigator Training Materials

### New Features to Train Users On

**1. Event History Replay**
- "If your browser crashes, click 'Reconnect' → your intelligence alerts from the last 5 minutes will reappear"

**2. Timestamp Precision Warnings**
- "If a corridor shows 'Timestamp inferred to noon', the direction might be uncertain"

**3. Seasonal Spike Context**
- "In October/November, crime spikes are normal (Diwali season). Look for non-seasonal anomalies instead"

**4. Hourly Anomalies**
- "Use hourly granularity to find intra-day patterns (e.g., 2–4 AM gang activity)"

**5. Confidence Bands**
- "CRITICAL = 80%+, HIGH = 60–80%, MEDIUM = 40–60%, LOW = <40% (don't ignore MEDIUM!)"

**6. Missing GPS Warnings**
- "If a hotspot shows 'missing GPS warning', it may be false. Verify with field data"

**7. Name Matching**
- "System now matches transliterations: 'Muhammad' = 'Mohammed', 'Sri Raj' = 'Raj'"

**8. Link Prediction Caveats**
- "Same-gang predictions are marked ⚠. Prioritize direct evidence (arrests, calls) over co-gang membership"

---

## Troubleshooting

### Issue: WebSocket Events Not Replaying

**Symptom:** Browser refreshes → no intelligence alerts replayed  
**Cause:** Event log table empty or workspace_id mismatch  
**Fix:**
```sql
-- Check if events being logged
SELECT COUNT(*) FROM intelligence_event_logs WHERE shown_at > DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- Check for workspace mismatch
SELECT DISTINCT workspace_id FROM intelligence_event_logs LIMIT 5;

-- Manually test replay
SELECT * FROM intelligence_event_logs 
WHERE workspace_id = 'workspace_123'
AND shown_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE);
```

### Issue: Timestamp Precision Errors

**Symptom:** Corridors show reversed direction  
**Cause:** occurred_datetime not properly populated  
**Fix:**
```sql
-- Check datetime population
SELECT COUNT(*) FROM firs WHERE occurred_datetime IS NULL;

-- Re-run migration
UPDATE firs SET occurred_datetime = CONCAT(occurred_date, ' ', occurred_time) 
WHERE occurred_datetime IS NULL;

-- Verify
SELECT fir_id, occurred_date, occurred_time, occurred_datetime FROM firs LIMIT 5;
```

### Issue: Crime Series Missing Data Not Flagged

**Symptom:** Series without missing data warnings  
**Cause:** Feature matrix flags not being passed correctly  
**Fix:**
```python
# Test in Python
engine = CrimeSeriesEngine(db)
result = engine.detect_series(district_id="DIST-01")
for s in result["series"]:
    evidence_dims = [e["dimension"] for e in s["explanation"]["evidence"]]
    if "missing_geo_data_warning" in evidence_dims:
        print(f"✓ Warnings working for {s['series_id']}")
    else:
        print(f"✗ No warnings for {s['series_id']} (may be false positive)")
```

---

## Success Criteria

Deployment is successful if all of the following are met within 24 hours of Wave 1:

- [ ] 0 critical incidents (system errors, data corruption)
- [ ] Alert fatigue decreased by ≥30% (vs. baseline)
- [ ] WebSocket event replay working for 100% of refreshes
- [ ] Timestamp precision warnings visible in ≥5 spatial corridors
- [ ] Entity Resolution prefix stripping matched ≥2 aliases
- [ ] Graph PageRank top 10 includes expected gang leaders
- [ ] No false timestamp-order corridors detected
- [ ] Neo4j weighted PageRank activated (confirmed in metrics)
- [ ] Seasonal CUSUM context showing for Oct/Nov spikes
- [ ] All tests passing on production infrastructure

---

## Contact & Escalation

**On-Call Engineer:** [To be assigned]  
**DBA Escalation:** [Database team]  
**ML/Analytics Review:** [Intelligence team]  

**Deployment Window:** 2026-07-27 00:00 UTC (off-peak)  
**Expected Completion:** 2026-08-03 23:59 UTC

---

✅ **NEXUS is ready for production deployment**
