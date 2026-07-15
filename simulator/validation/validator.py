"""
NEXUS Simulator — Simulation Validator
Runs comprehensive integrity checks across all generated datasets:
  - Foreign key integrity
  - No impossible timestamps
  - Coordinates within Karnataka
  - No orphan nodes in graph
  - Duplicate ID detection
  - Crime chronology order
  - Investigation chronology
Reports all issues without raising exceptions (soft validation).
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Set, Any, Optional

logger = logging.getLogger(__name__)

# Karnataka bounding box
KA_LAT_MIN, KA_LAT_MAX = 11.5, 18.5
KA_LNG_MIN, KA_LNG_MAX = 74.0, 78.6


@dataclass
class ValidationIssue:
    severity: str       # "ERROR" | "WARNING" | "INFO"
    check_name: str
    entity_id: str
    message: str


class SimulationValidator:
    """
    Validates all simulation outputs for consistency and correctness.
    Accumulates issues and produces a summary report.
    """

    def __init__(self) -> None:
        self.issues: List[ValidationIssue] = []

    def _issue(self, severity: str, check: str, entity_id: str, msg: str) -> None:
        self.issues.append(ValidationIssue(severity, check, entity_id, msg))

    # ──────────────────────────────────────────────────────────────────────
    # Individual checks
    # ──────────────────────────────────────────────────────────────────────

    def check_fir_coordinates(self, firs: list) -> int:
        """All FIR coordinates must be within Karnataka bounding box."""
        errors = 0
        for fir in firs:
            if not (KA_LAT_MIN <= fir.latitude <= KA_LAT_MAX):
                self._issue("ERROR", "coordinate_bounds", fir.fir_id,
                            f"Latitude {fir.latitude} out of Karnataka bounds")
                errors += 1
            if not (KA_LNG_MIN <= fir.longitude <= KA_LNG_MAX):
                self._issue("ERROR", "coordinate_bounds", fir.fir_id,
                            f"Longitude {fir.longitude} out of Karnataka bounds")
                errors += 1
        return errors

    def check_fir_chronology(self, firs: list) -> int:
        """Reported date must not precede occurred date."""
        errors = 0
        for fir in firs:
            if fir.reported_date < fir.occurred_date:
                self._issue("ERROR", "chronology", fir.fir_id,
                            f"Reported date {fir.reported_date} before occurred {fir.occurred_date}")
                errors += 1
        return errors

    def check_fir_station_fk(self, firs: list, station_ids: Set[str]) -> int:
        """All FIR station_ids must exist in stations table."""
        errors = 0
        for fir in firs:
            if fir.station_id not in station_ids:
                self._issue("ERROR", "fk_station", fir.fir_id,
                            f"Station {fir.station_id} not found")
                errors += 1
        return errors

    def check_fir_officer_fk(self, firs: list, officer_ids: Set[str]) -> int:
        """FIR investigating_officer_id must exist (if not null)."""
        errors = 0
        for fir in firs:
            if fir.investigating_officer_id and fir.investigating_officer_id not in officer_ids:
                self._issue("WARNING", "fk_officer", fir.fir_id,
                            f"Officer {fir.investigating_officer_id} not found")
                errors += 1
        return errors

    def check_duplicate_ids(self, items: list, id_field: str) -> int:
        """No two records should share the same ID."""
        seen: Set[str] = set()
        errors = 0
        for item in items:
            eid = getattr(item, id_field, None)
            if eid in seen:
                self._issue("ERROR", "duplicate_id", str(eid),
                            f"Duplicate {id_field}: {eid}")
                errors += 1
            else:
                seen.add(eid)
        return errors

    def check_criminal_station_fk(self, criminals: list, station_ids: Set[str]) -> int:
        """All criminal home station_ids must exist."""
        errors = 0
        for c in criminals:
            if c.station_id not in station_ids:
                self._issue("WARNING", "fk_criminal_station", c.criminal_id,
                            f"Criminal {c.criminal_id} references unknown station {c.station_id}")
                errors += 1
        return errors

    def check_arrest_fir_fk(self, arrests: list, fir_ids: Set[str]) -> int:
        """All arrest records must reference valid FIR IDs."""
        errors = 0
        for a in arrests:
            if a.fir_id not in fir_ids:
                self._issue("ERROR", "fk_arrest_fir", a.arrest_id,
                            f"Arrest {a.arrest_id} references unknown FIR {a.fir_id}")
                errors += 1
        return errors

    def check_arrest_chronology(self, arrests: list, fir_map: Dict[str, Any]) -> int:
        """Arrest date must not precede FIR reported date."""
        errors = 0
        for a in arrests:
            fir = fir_map.get(a.fir_id)
            if fir and a.arrest_date < fir.reported_date:
                self._issue("ERROR", "arrest_chronology", a.arrest_id,
                            f"Arrest {a.arrest_date} before FIR report {fir.reported_date}")
                errors += 1
        return errors

    def check_evidence_fir_fk(self, evidence: list, fir_ids: Set[str]) -> int:
        """All evidence records must reference valid FIR IDs."""
        errors = 0
        for e in evidence:
            if e.fir_id not in fir_ids:
                self._issue("ERROR", "fk_evidence_fir", e.evidence_id,
                            f"Evidence {e.evidence_id} references unknown FIR {e.fir_id}")
                errors += 1
        return errors

    def check_graph_connectivity(self, graph) -> int:
        """Warn about nodes with no edges (orphan nodes)."""
        if not graph.G:
            return 0
        try:
            import networkx as nx
            orphans = [n for n in graph.G.nodes() if graph.G.degree(n) == 0]
            if orphans:
                self._issue("WARNING", "orphan_nodes", "GRAPH",
                            f"{len(orphans)} orphan nodes (no edges)")
            return len(orphans)
        except Exception:
            return 0

    def check_station_coordinates(self, stations: list) -> int:
        """All stations must have coordinates within Karnataka."""
        errors = 0
        for s in stations:
            if not (KA_LAT_MIN <= s.latitude <= KA_LAT_MAX):
                self._issue("ERROR", "station_coords", s.station_id,
                            f"Station lat {s.latitude} out of bounds")
                errors += 1
            if not (KA_LNG_MIN <= s.longitude <= KA_LNG_MAX):
                self._issue("ERROR", "station_coords", s.station_id,
                            f"Station lng {s.longitude} out of bounds")
                errors += 1
        return errors

    # ──────────────────────────────────────────────────────────────────────
    # Master validation runner
    # ──────────────────────────────────────────────────────────────────────

    def validate_all(
        self,
        stations: list,
        officers: list,
        criminals: list,
        firs: list,
        arrests: list,
        evidence: list,
        graph=None,
    ) -> dict:
        """Run all validation checks and return summary."""
        logger.info("Running simulation validation...")
        self.issues = []

        station_ids = {s.station_id for s in stations}
        officer_ids = {o.officer_id for o in officers}
        fir_ids     = {f.fir_id for f in firs}
        fir_map     = {f.fir_id: f for f in firs}

        results = {}
        results["coord_errors"]        = self.check_fir_coordinates(firs)
        results["chronology_errors"]   = self.check_fir_chronology(firs)
        results["station_fk_errors"]   = self.check_fir_station_fk(firs, station_ids)
        results["officer_fk_warnings"] = self.check_fir_officer_fk(firs, officer_ids)
        results["duplicate_fir_ids"]   = self.check_duplicate_ids(firs, "fir_id")
        results["criminal_fk_errors"]  = self.check_criminal_station_fk(criminals, station_ids)
        results["arrest_fk_errors"]    = self.check_arrest_fir_fk(arrests, fir_ids)
        results["arrest_chrono_errors"]= self.check_arrest_chronology(arrests, fir_map)
        results["evidence_fk_errors"]  = self.check_evidence_fir_fk(evidence, fir_ids)
        results["station_coord_errors"]= self.check_station_coordinates(stations)
        if graph:
            results["orphan_nodes"] = self.check_graph_connectivity(graph)

        total_errors = sum(
            v for k, v in results.items() if "error" in k.lower()
        )
        total_warnings = sum(
            v for k, v in results.items() if "warning" in k.lower()
        )

        logger.info(f"Validation complete: {total_errors} errors, {total_warnings} warnings")
        return {
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "checks": results,
            "passed": total_errors == 0,
        }

    def report(self) -> str:
        """Return a human-readable validation report."""
        if not self.issues:
            return "✅ All validation checks passed.\n"

        lines = [f"{'SEV':<10} {'CHECK':<25} {'ENTITY':<25} MESSAGE"]
        lines.append("-" * 100)
        for issue in self.issues[:100]:  # Cap at 100 for readability
            lines.append(
                f"{issue.severity:<10} {issue.check_name:<25} {issue.entity_id[:24]:<25} {issue.message}"
            )
        if len(self.issues) > 100:
            lines.append(f"... and {len(self.issues) - 100} more issues.")
        return "\n".join(lines)
