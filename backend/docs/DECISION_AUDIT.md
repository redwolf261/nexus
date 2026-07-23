# Decision Audit & Legal Reproducibility (Phase 8.2 Milestone 5)

## Overview

Milestone 5 establishes 100% legal defensibility and auditability for every investigation assignment decision.

## Immutable Data Stores

1. **`assignment_decision_histories`** (Append-Only):
   - Never updated or deleted.
   - Captures decision type (`ACCEPT`, `OVERRIDE`, `REJECT`, `DEFER`), chosen officer, supervisor ID, override reason, free-text justification (min 50 chars), policy violations, approval chain, and policy version.

2. **`recommendation_snapshots`** (Persisted Candidate State):
   - Captures exact ranked candidates, scores, component weights, workload snapshot, and policy version at the moment of decision.
   - Guarantees future legal reproducibility: any past recommendation can be re-instantiated and inspected with byte-exact precision.
