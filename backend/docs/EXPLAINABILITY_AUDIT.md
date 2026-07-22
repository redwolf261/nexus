# Explainability Audit Report
**Phase 7.2 Independent Scientific Audit**

## 1. Provenance Chain Verification
The audit examined the execution trace from backend algorithm to React UI rendering to verify that the 6-stage provenance model is unbroken.

### The 6-Stage Requirement
1. **Observation exists:** Yes. Passed via `observation` string.
2. **Evidence exists:** Yes. Passed via `evidence` array of `EvidenceItem` objects.
3. **Analytical Rule exists:** Yes. Passed via `analytical_rule` string.
4. **Inference exists:** Yes. Passed via `inference` string.
5. **Confidence exists:** Yes. Passed via `confidence` nested object.
6. **Recommended Action exists:** Yes. Passed via optional `recommended_action` string.

## 2. API Contract Audit
By statically analyzing the Pydantic schemas in `backend/intelligence/explainability.py` and the FastAPI routers in `backend/api/routers/intelligence.py`, we confirm:
- **No skipping:** It is impossible for the backend to return an HTTP 200 containing intelligence without satisfying the `IntelligenceExplanation` schema. Pydantic enforces this strictly.
- **Opaque Scores:** Are eliminated. Raw float metrics (e.g. `pagerank = 0.045`) are wrapped in explanations before being serialized.

## 3. UI Rendering Audit
- **Trace:** Workspace -> `useLiveWorkspace.ts` -> `applyEventReducer` -> React Query `['workspace']` -> `IntelligencePanel` -> `ExplainabilityCard`.
- **Verdict:** The `ExplainabilityCard.tsx` component strictly consumes the exact 6-stage schema. Nothing is dropped.
- **Flaw Detected:** The React Query state cache `analytical_findings` is completely overwritten on hard refreshes. While the intelligence is persisted in PostgreSQL, the WebSocket event history is not replayed upon reconnection, meaning transient UI alerts might be missed if the analyst refreshes the browser.

## 4. Legal / Prosecutorial Utility
- **Would a prosecutor defend this?** Yes. Because the `analytical_rule` and `evidence` weights are exposed in the JSON, the logic is deterministic and interrogatable. If the defense asks "Why did the system link my client to this crime series?", the exact 10-dimensional DBSCAN logic and exact shared features are permanently recorded in the `IntelligenceExplanation`. There are no "black box neural network" hallucinations.
