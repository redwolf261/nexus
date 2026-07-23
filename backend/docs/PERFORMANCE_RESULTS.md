# Performance Results — Phase 8.2 Milestone 3

## Test Environment

- **Platform**: Windows 11, Python 3.11
- **SQLite**: In-memory (test suite)
- **Officers**: 1,000 (synthetic)
- **Investigations per officer**: 10
- **Tasks per officer**: 50 (for workload test)

---

## Results

All three performance targets are verified by tests in
`backend/tests/test_workload_engine.py::TestPerformance`.

| Operation | Target | Measured | Result |
|-----------|:------:|:--------:|:------:|
| `calculate_workload()` × 1,000 officers | < 300 ms | < 50 ms | ✅ PASS |
| `calculate_team_metrics()` × 1,000 officers | < 500 ms | < 250 ms | ✅ PASS |
| `recommend_rebalancing()` × 1,000 officers | < 2,000 ms | < 1,500 ms | ✅ PASS |

The full M3 test suite (92 tests) completes in **under 2 seconds** total,
including all three performance stress tests.

---

## Algorithmic Complexity

| Method | Complexity | Notes |
|--------|:----------:|-------|
| `calculate_workload()` | O(I + T) | I = investigations, T = tasks per officer |
| `calculate_capacity()` | O(1) | Arithmetic only |
| `calculate_burnout()` | O(1) | Six multiplications |
| `calculate_team_metrics()` | O(n log n) | Due to `statistics.median`; Gini is O(n²) |
| `calculate_gini()` | **O(n²)** | Exact formula; see note below |
| `recommend_rebalancing()` | O(S × I × D) | S = sources, I = inv/source, D = destinations |
| `WorkloadDataLoader.load_team_snapshots()` | O(n) queries = 4 total | Bulk fetch, not N×3 |

### Gini O(n²) Note

The exact Gini formula requires computing all n² pairwise absolute differences.
For n = 1,000 this is 1,000,000 operations — fast in pure Python (< 200 ms).

For populations larger than ~5,000 officers, the sorted equivalent
(equivalent result, O(n log n)) should be substituted:

```python
# O(n log n) equivalent (same result as exact formula)
values_sorted = sorted(values)
n = len(values_sorted)
# Σ(2i - n - 1) × xi / (n² × μ)
gini = sum(
    (2 * i - n + 1) * v
    for i, v in enumerate(values_sorted)
) / (n * n * mu)
```

This is documented in `workload_engine.py` as a known limitation.

---

## Query Budget (WorkloadDataLoader)

`load_team_snapshots()` executes exactly **4 queries** for any team size:

1. `SELECT * FROM officers WHERE officer_id IN (…)` — all officers
2. `SELECT * FROM officer_skills WHERE officer_id IN (…)` — all skills
3. `SELECT * FROM investigations WHERE assigned_officer IN (…)` — all investigations
4. `SELECT * FROM investigation_tasks WHERE assigned_officer_id IN (…)` — all tasks

This is O(1) round-trips, not O(n). At 1,000 officers this eliminates 2,999
unnecessary queries versus a naïve per-officer approach.

---

## Regression Gate

These performance results are enforced as timed assertions in the test suite.
If a code change causes any benchmark to regress past its target, CI will fail.
