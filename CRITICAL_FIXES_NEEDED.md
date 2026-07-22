# Critical Fixes Required - Phase 7.1 & 7.2

**Priority:** BEFORE Phase 8 Launch  
**Estimated Total Effort:** 3–4 developer-days  
**Risk if Deferred:** Legal liability, audit trail gaps, rank errors  

---

## FIX #1 - CRITICAL: Spatial Corridors Unreliable (Day-Level Timestamps)

**Problem:** FIR timestamps lack hour/minute precision → corridor direction inference is reversed  
**Risk:** Spatial evidence inadmissible in court  
**Effort:** MEDIUM (2 days)

### Implementation Plan

#### Step 1: Extend FIR Schema
```python
# backend/db/schema.py - FIR table

class FIR(Base):
    __tablename__ = "firs"
    # ... existing columns ...
    occurred_date = Column(Date)          # Existing: date only
    occurred_time = Column(Time)          # NEW: hour:minute:second
    occurred_datetime = Column(DateTime)  # NEW: combined for easy sorting
```

**Migration Script:**
```python
# backend/migrations/add_fir_timestamp_precision.py
"""
Populate occurred_time from existing FIR data:
- If FIRs have time info in description, parse it
- Otherwise, default to 12:00 (noon)
- Compute occurred_datetime = occurred_date + occurred_time
"""
```

#### Step 2: Update Spatial Analytics
```python
# backend/intelligence/spatial_analytics.py - Line 104-134

def detect_travel_corridors(self, criminal_id: str) -> Dict[str, Any]:
    """Updated: Use occurred_datetime for chronological ordering."""
    firs = (
        self.db.query(FIR)
        .filter(FIR.fir_id.in_(fir_ids))
        .filter(FIR.latitude.isnot(None), FIR.longitude.isnot(None))
        .order_by(FIR.occurred_datetime)  # CHANGED: from occurred_date → occurred_datetime
        .all()
    )
    
    # Add timestamp precision warning
    for f in firs:
        if f.occurred_time.hour == 12 and f.occurred_time.minute == 0:
            # Flag as "inferred noon time" (potential unreliability)
            evidence.append(EvidenceItem(
                dimension="timestamp_precision_warning",
                description=f"FIR timestamp inferred to noon (no hour precision)",
                raw_value="inferred",
                weight=0.0,
                contributed_score=0.0,
            ))
```

#### Step 3: Add Evidence & Confidence Penalty
```python
# Lines 129-145 (corridor creation)
# If ANY FIR in corridor sequence has inferred time:
#   - Reduce corridor confidence from 0.90 → 0.70
#   - Add evidence: "Timestamp precision affects directional inference"

if any(f.occurred_time.hour == 12 for f in [f1, f2]):
    conf.recency_weight *= 0.7  # Penalize low precision
    evidence.append(EvidenceItem(...))
```

**Migration Checklist:**
- [ ] Add `occurred_time`, `occurred_datetime` columns to FIR table
- [ ] Backfill existing FIRs (parse time from description or default to noon)
- [ ] Update `spatial_analytics.py` to use `occurred_datetime`
- [ ] Add confidence penalty for inferred times
- [ ] Test with existing corridors (verify direction doesn't flip)
- [ ] Update API contract in `ANALYTICAL_ENGINE.md`

**Tests Needed:**
- Test case: FIR-A (2026-07-15 11 PM) → FIR-B (2026-07-16 6 AM) should order correctly
- Test case: Missing time should be flagged in evidence
- Regression: Existing corridors shouldn't flip direction

---

## FIX #2 - CRITICAL: WebSocket Event History Lost on Reconnection

**Problem:** Browser refresh loses intelligence alerts forever; no audit trail  
**Risk:** Compliance issue; can't prove what was shown to analyst  
**Effort:** MEDIUM (2 days)

### Implementation Plan

#### Step 1: Add Event Log Table
```python
# backend/db/schema.py

class IntelligenceEventLog(Base):
    """Audit trail of all intelligence shown to analysts."""
    __tablename__ = 'intelligence_event_logs'
    
    event_id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey('investigations.id'), index=True)
    event_type = Column(String)  # SERIES_DETECTED, LINK_FOUND, ANOMALY, etc.
    entity_id = Column(String, index=True)
    confidence_score = Column(Float)
    explanation_json = Column(JSON)  # Full IntelligenceExplanation
    shown_at = Column(DateTime, default=func.now(), index=True)
    analyst_id = Column(String, nullable=True)  # Who saw it
    dismissed_at = Column(DateTime, nullable=True)  # When analyst dismissed
```

#### Step 2: Update WebSocket Event Dispatcher
```python
# backend/api/routers/ws.py

async def broadcast_intelligence_event(workspace_id: str, event: Dict):
    """
    1. Log event to intelligence_event_logs table
    2. Broadcast to connected WebSocket clients
    3. Return event_id for acknowledgment
    """
    event_id = f"EVT-{uuid.uuid4().hex[:8]}"
    
    # Log to DB
    log_entry = IntelligenceEventLog(
        event_id=event_id,
        workspace_id=workspace_id,
        event_type=event["type"],
        entity_id=event.get("entity_id"),
        confidence_score=event.get("confidence"),
        explanation_json=event.get("explanation"),
        analyst_id=get_current_analyst_id(),
    )
    db.add(log_entry)
    db.commit()
    
    # Broadcast via WebSocket
    message = {"event_id": event_id, "data": event}
    await manager.broadcast(workspace_id, message)
    
    return event_id
```

#### Step 3: Implement Event Replay on Reconnection
```python
# backend/api/routers/ws.py - WebSocket connection handler

@router.websocket("/ws/investigations/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    await manager.connect(workspace_id, websocket)
    
    # NEW: Replay events from last 5 minutes
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    
    recent_events = db.query(IntelligenceEventLog).filter(
        IntelligenceEventLog.workspace_id == workspace_id,
        IntelligenceEventLog.shown_at >= cutoff,
    ).order_by(IntelligenceEventLog.shown_at).all()
    
    for event in recent_events:
        await websocket.send_json({
            "type": "REPLAY",
            "event_id": event.event_id,
            "data": event.explanation_json,
        })
    
    # Continue normal WebSocket loop
    try:
        while True:
            data = await websocket.receive_text()
            # ... handle incoming messages ...
    except WebSocketDisconnect:
        manager.disconnect(workspace_id, websocket)
```

#### Step 4: Update Frontend to Handle Replay
```typescript
// frontend/components/investigation/useLiveWorkspace.ts

useEffect(() => {
  const ws = new WebSocket(`ws://localhost/ws/investigations/${workspaceId}`);
  
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    if (msg.type === "REPLAY") {
      // UI renders replayed events in different color (faded)
      dispatch({
        type: "APPEND_INTELLIGENCE",
        payload: { ...msg.data, is_replayed: true }
      });
    } else {
      // Normal real-time event
      dispatch({
        type: "APPEND_INTELLIGENCE",
        payload: msg.data
      });
    }
  };
}, [workspaceId]);
```

**Migration Checklist:**
- [ ] Add `IntelligenceEventLog` table to schema
- [ ] Update `broadcast_intelligence_event()` to log all events
- [ ] Implement replay logic in WebSocket connection handler
- [ ] Update frontend to render replayed events
- [ ] Test: Refresh browser → see last 5 min of intelligence replayed
- [ ] Test: Disconnect/reconnect → events persist

**Tests Needed:**
- Test event logging: create intelligence → verify DB entry
- Test replay: disconnect WebSocket, reconnect → see replay
- Test filtering: only replay events from this workspace
- Regression: normal real-time events still work

---

## FIX #3 - HIGH: DBSCAN Vulnerable to Missing Data

**Problem:** NULL coordinates collapse to (0,0) → artificial density → false clusters  
**Risk:** False crime series alerts  
**Effort:** MEDIUM (1.5 days)

### Implementation Plan

#### Option A (Conservative): Exclude Missing Features
```python
# backend/intelligence/crime_series.py - _build_feature_matrix()

def _build_feature_matrix(self, firs: List[FIR]):
    """Separate clustering runs for complete vs. incomplete data."""
    
    # Split FIRs by data completeness
    firs_with_geo = [f for f in firs if f.latitude and f.longitude]
    firs_no_geo   = [f for f in firs if not f.latitude or not f.longitude]
    
    if len(firs_with_geo) >= DBSCAN_MIN_SAMPLES:
        # Cluster with 8 features (exclude geo)
        features_geo = [...geo features...]
    
    if len(firs_no_geo) >= DBSCAN_MIN_SAMPLES:
        # Cluster with 8 features (no geo dimensions)
        features_no_geo = [...non-geo features...]
    
    # Merge results, annotate each cluster's data quality
```

#### Option B (Current Best - Phase 7.3 Path): Flag in Evidence
```python
# Already implemented in Phase 7.3 spatial_analytics.py
# Just apply same logic to crime_series.py

# Add to Crime Series evidence:
if any(f.latitude is None or f.longitude is None for f in cluster_firs):
    evidence.append(EvidenceItem(
        dimension="missing_geo_data",
        description=f"{missing_count}/{len(cluster_firs)} FIRs lack GPS → potential false cluster",
        raw_value=missing_count,
        weight=0.0,
        contributed_score=0.0,
    ))
    # Reduce confidence if too many missing
    if missing_count / len(cluster_firs) > 0.5:
        conf = ConfidenceScore(
            evidence_quality=conf.evidence_quality * 0.7,  # Penalize
            ...
        ).compute()
```

**Recommendation:** Use **Option B** (already done in Phase 7.3) + add to Crime Series

**Migration Checklist:**
- [ ] Update `crime_series.py` to detect missing geo data
- [ ] Add evidence flag when > 50% of cluster lacks GPS
- [ ] Reduce confidence score proportionally
- [ ] Test: cluster with half missing GPS → verify confidence lower

---

## FIX #4 - HIGH: Jaro-Winkler Threshold Too Strict

**Problem:** NAME_SIMILARITY_MIN = 0.75 misses 19% of real aliases (False Negatives)  
**Risk:** Criminals evade via name variation  
**Effort:** LOW (0.5 days)

### Implementation Plan

#### Step 1: Lower Threshold
```python
# backend/intelligence/evidence_weights.py

- NAME_SIMILARITY_MIN: float = 0.75
+ NAME_SIMILARITY_MIN: float = 0.70  # More lenient for Indian names
```

#### Step 2: Add Regional Variant Detector
```python
# backend/intelligence/entity_resolution.py

def _strip_regional_prefix(name: str) -> str:
    """Remove common regional prefixes for comparison."""
    prefixes = ["Sri ", "Shri ", "Dr ", "Dr. ", "Md ", "Muhammad ", "Md. "]
    for prefix in prefixes:
        if name.lower().startswith(prefix.lower()):
            return name[len(prefix):]
    return name

# In _score_person_pair():
source_stripped = _strip_regional_prefix(source.name_en or "")
candidate_stripped = _strip_regional_prefix(candidate.name_en or "")
name_sim_stripped = _jaro_winkler(source_stripped, candidate_stripped)

if name_sim_stripped >= 0.70:  # Lower threshold on stripped names
    evidence.append(EvidenceItem(
        dimension="name_regional_variant",
        description=f"Name match after stripping regional prefix: {source_stripped} ~ {candidate_stripped}",
        ...
    ))
```

**Migration Checklist:**
- [ ] Change `NAME_SIMILARITY_MIN = 0.70`
- [ ] Add `_strip_regional_prefix()` function
- [ ] Test: "Sri Raj" vs "Raj" should now match
- [ ] Test: Precision/Recall on test set (~93%/84% target)
- [ ] Verify no new false positives on common names

**Tests Needed:**
- Test: "Muhammad Hassan" vs "Mohammed Hassan" → match
- Test: "Sri Rajesh" vs "Rajesh" → match
- Test: "John Doe" vs "John Smith" → no match

---

## FIX #5 - HIGH: Missing Edge Weighting in Graph Analytics

**Problem:** All Neo4j relationships treated equally (1 phone call = 50 co-arrests)  
**Risk:** Rank errors; low-level dealers ranked higher than gang boss  
**Effort:** HIGH (2.5 days)

### Implementation Plan

#### Step 1: Add Relationship Metadata to Neo4j
```python
# backend/intelligence/graph_analytics.py - or new migration

"""
Update Neo4j relationships to include strength metadata:
MATCH (a)-[r:ASSOCIATED_WITH]->(b)
SET r.strength = coalesce(r.strength, 1),  # Start at 1
    r.relationship_types = coalesce(r.relationship_types, [])
"""

# When loading data, increment strength for repeated associations
if_already_connected:
    relationship.strength += 1
    relationship.last_associated = today()
```

#### Step 2: Modify PageRank to Weight Edges
```python
# backend/intelligence/graph_analytics.py - _compute_pagerank()

def _compute_pagerank(self, max_nodes: int) -> int:
    """Weighted PageRank: high-strength edges propagate more influence."""
    query = """
    MATCH (n:Person)-[r:COMMITTED|MEMBER_OF|ASSOCIATED_WITH]-(m:Person)
    WHERE r.strength >= 3  // Only strong relationships
    WITH n, m, r.strength as weight
    WITH n, sum(weight) as total_weight
    RETURN n.id AS entity_id, total_weight as weighted_degree
    ORDER BY weighted_degree DESC
    """
    results = self._neo4j.query(query, {"max_nodes": max_nodes})
    # Normalize by total_weight instead of unweighted degree
```

#### Step 3: Add Evidence Showing Relationship Strength
```python
# In link_prediction() and graph metrics explanations

evidence.append(EvidenceItem(
    dimension="relationship_strength",
    description=f"Link type: {r.relationship_type}, co-occurrences: {r.strength}",
    raw_value=r.strength,
    weight=0.5,
    contributed_score=min(1.0, r.strength / 10),  # Scale by strength
))
```

**Migration Checklist:**
- [ ] Add `strength` and `relationship_types` properties to Neo4j relationships
- [ ] Backfill strength from FIR co-arrest counts
- [ ] Update PageRank to weight edges by strength
- [ ] Update Link Prediction to use weighted edges
- [ ] Add evidence showing relationship strength
- [ ] Test: high-strength edges (gang boss) rank above low-strength (dealer)

**Tests Needed:**
- Inject test data: Person A (10 edges, strength=1 each), Person B (5 edges, strength=5 each)
- Verify: Person B ranks higher despite lower node degree
- Regression: Existing rankings shouldn't flip dramatically

---

## Summary: Fix Roadmap

| Fix | Priority | Effort | Timeline | Dependencies |
|-----|----------|--------|----------|--------------|
| #1: Spatial timestamps | CRITICAL | 2 days | Week 1 | Backfill FIR times |
| #2: WebSocket replay | CRITICAL | 2 days | Week 1 | Event log table |
| #3: Missing data in DBSCAN | HIGH | 1.5 days | Week 1 | (Phase 7.3 partial fix) |
| #4: Jaro-Winkler threshold | HIGH | 0.5 days | Week 1 | Test suite |
| #5: Edge weighting | HIGH | 2.5 days | Week 2 | Neo4j backfill |

**Total Effort:** 8.5 developer-days  
**Recommended Timeline:** 2 weeks (one person) or 1 week (two people)

**Blocker Status:** Fix #1 & #2 must complete before Phase 8 launch. Fixes #3, #4, #5 can defer to 8.1 if timeline tight.
