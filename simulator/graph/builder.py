"""
NEXUS Simulator — Crime Knowledge Graph Builder
Assembles a NetworkX heterogeneous graph from all simulation entities.
Supports:
  - Node types: Person, Vehicle, FIR, Phone, Gang, Evidence, Station, District, Officer
  - Edge types: all 20 from relationships.py
"""
from __future__ import annotations
import logging
from typing import List, Dict, Optional, Any

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from simulator.crimes.fir import FIR, Accused, Victim
from simulator.criminals.profiles import CriminalProfile
from simulator.criminals.gangs import Gang
from simulator.investigations.evidence import Evidence
from simulator.geography.karnataka import Station
from simulator.population.officers import Officer

logger = logging.getLogger(__name__)


class CrimeKnowledgeGraph:
    """
    Builds and holds the heterogeneous crime knowledge graph.
    Falls back to a plain dict-of-dicts if NetworkX is unavailable.
    """

    def __init__(self) -> None:
        if HAS_NETWORKX:
            self.G = nx.MultiDiGraph()
        else:
            self.G = None
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self._node_types: Dict[str, str] = {}

    def _add_node(self, node_id: str, node_type: str, **props) -> None:
        self.nodes[node_id] = {"id": node_id, "type": node_type, **props}
        self._node_types[node_id] = node_type
        if self.G is not None:
            self.G.add_node(node_id, node_type=node_type, **props)

    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        **props,
    ) -> None:
        edge = {
            "source": source_id,
            "target": target_id,
            "relation": relation,
            "weight": weight,
            **props,
        }
        self.edges.append(edge)
        if self.G is not None:
            self.G.add_edge(source_id, target_id, relation=relation, weight=weight, **props)

    # ──────────────────────────────────────────────────────────────────────
    # Node population methods
    # ──────────────────────────────────────────────────────────────────────

    def add_criminals(self, criminals: List[CriminalProfile]) -> None:
        logger.info(f"Adding {len(criminals)} criminal nodes...")
        for c in criminals:
            self._add_node(
                c.criminal_id, "Person",
                name=c.name_en, name_kn=c.name_kn,
                age=c.age, gender=c.gender,
                district_id=c.district_id, risk_level=c.risk_level,
                expertise=c.expertise, career_stage=c.career_stage,
            )

    def add_gangs(self, gangs: List[Gang]) -> None:
        logger.info(f"Adding {len(gangs)} gang nodes...")
        for g in gangs:
            self._add_node(
                g.gang_id, "Gang",
                name=g.name, specialization=g.specialization,
                threat_level=g.threat_level, num_members=g.num_members,
                is_active=g.is_active,
            )
            # Gang membership edges
            for mid in g.member_criminal_ids:
                if mid == g.leader_criminal_id:
                    self._add_edge(mid, g.gang_id, "LEADS", weight=1.0)
                else:
                    self._add_edge(mid, g.gang_id, "MEMBER_OF", weight=1.0)
            # Territory edges
            for dist_id in g.territory_district_ids:
                if dist_id not in self.nodes:
                    self._add_node(dist_id, "District", name=dist_id)
                self._add_edge(g.gang_id, dist_id, "OPERATES_IN", weight=1.0)

    def add_stations(self, stations: List[Station]) -> None:
        logger.info(f"Adding {len(stations)} station nodes...")
        for s in stations:
            self._add_node(
                s.station_id, "Station",
                name=s.name, district_id=s.district_id,
                lat=s.latitude, lng=s.longitude,
            )

    def add_officers(self, officers: List[Officer]) -> None:
        logger.info(f"Adding {len(officers)} officer nodes...")
        for o in officers:
            self._add_node(
                o.officer_id, "Officer",
                name=o.name_en, rank=o.rank,
                station_id=o.station_id,
            )

    def add_firs(
        self,
        firs: List[FIR],
        criminals_map: Dict[str, CriminalProfile],
    ) -> None:
        logger.info(f"Adding {len(firs)} FIR nodes...")
        for fir in firs:
            self._add_node(
                fir.fir_id, "FIR",
                fir_number=fir.fir_number,
                crime_type=fir.crime_type,
                severity=fir.severity,
                district_id=fir.district_id,
                occurred_date=str(fir.occurred_date),
                status=fir.status,
                estimated_loss=fir.estimated_loss_inr,
                lat=fir.latitude, lng=fir.longitude,
            )

            # FIR → Station
            self._add_edge(fir.fir_id, fir.station_id, "REGISTERED_AT", weight=1.0)

            # FIR → IO
            if fir.investigating_officer_id:
                self._add_edge(fir.fir_id, fir.investigating_officer_id, "INVESTIGATED_BY", weight=1.0)

            # Criminal → FIR (COMMITTED)
            if fir.primary_criminal_id and fir.primary_criminal_id in criminals_map:
                self._add_edge(
                    fir.primary_criminal_id, fir.fir_id, "COMMITTED",
                    weight=0.9,
                    is_gang_crime=fir.is_gang_crime,
                )

            # Accomplices → FIR (ACCOMPLICE_IN)
            for acc_id in fir.accomplice_criminal_ids:
                if acc_id in criminals_map:
                    self._add_edge(acc_id, fir.fir_id, "ACCOMPLICE_IN", weight=0.8)

            # Vehicle → FIR
            for vid in fir.vehicle_ids:
                if vid not in self.nodes:
                    self._add_node(vid, "Vehicle", registration=vid)
                self._add_edge(vid, fir.fir_id, "USED_VEHICLE_IN", weight=0.85)

            # Phone → FIR
            for pid in fir.phone_ids:
                if pid not in self.nodes:
                    self._add_node(pid, "Phone", number=pid)
                self._add_edge(pid, fir.fir_id, "PHONE_LINKED_TO", weight=0.75)

            # Gang → FIR (implicit via criminal)
            if fir.gang_id:
                self._add_edge(fir.gang_id, fir.fir_id, "COMMITTED", weight=0.8)

            # Victim nodes
            for victim in fir.victims:
                vid_node = f"VIC-{victim.victim_id}"
                if vid_node not in self.nodes:
                    self._add_node(
                        vid_node, "Person",
                        name=victim.name_en, role="victim",
                        gender=victim.gender, age=victim.age,
                    )
                self._add_edge(vid_node, fir.fir_id, "VICTIM_IN", weight=1.0)

    def add_evidence(self, evidence_list: List[Evidence]) -> None:
        logger.info(f"Adding {len(evidence_list)} evidence nodes...")
        for ev in evidence_list:
            self._add_node(
                ev.evidence_id, "Evidence",
                evidence_type=ev.evidence_type,
                description=ev.description[:100],
                fir_id=ev.fir_id,
                is_forensic=ev.is_forensic,
                condition=ev.condition,
            )
            self._add_edge(ev.evidence_id, ev.fir_id, "EVIDENCE_FOR", weight=1.0)

    def add_associate_edges(self, criminals: List[CriminalProfile]) -> None:
        """Add known-associates edges between criminals."""
        for c in criminals:
            for assoc_id in c.known_associates[:5]:  # Cap at 5 per criminal
                if assoc_id in self.nodes:
                    self._add_edge(
                        c.criminal_id, assoc_id, "ASSOCIATED_WITH",
                        weight=0.7,
                    )

    def stats(self) -> dict:
        return {
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "node_types": {
                t: sum(1 for v in self._node_types.values() if v == t)
                for t in set(self._node_types.values())
            },
        }
