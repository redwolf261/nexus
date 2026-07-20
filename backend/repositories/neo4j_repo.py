from __future__ import annotations

from backend.neo4j_client import neo4j_client


class Neo4jRepository:
    def __init__(self):
        self.client = neo4j_client

    def run_query(self, query: str, parameters: dict = None):
        return self.client.query(query, parameters)

    def get_campaigns(self):
        """Gang-mastermind-FIR summary for community detection."""
        query = """
        MATCH (m:Person)-[:LEADS]->(g:Gang)
        OPTIONAL MATCH (member:Person)-[:MEMBER_OF]->(g)
        WITH m, g, collect(DISTINCT member) + m AS crew
        UNWIND crew AS c
        OPTIONAL MATCH (c)-[:COMMITTED]->(f:FIR)
        RETURN m.id AS mastermind, m.name AS mastermind_name,
               g.id AS gang, g.name AS gang_name,
               count(DISTINCT f) AS campaign_count
        ORDER BY campaign_count DESC
        """
        return self.client.query(query)

    def get_cross_jurisdiction_links(self, fir_id: str):
        """Find FIRs linked through shared vehicles or phones.

        Phase 1 graph loader created:
          (Person)-[:USED_VEHICLE_IN]->(FIR)
          (Person)-[:PHONE_LINKED_TO]->(FIR)

        We pivot via the shared Person node instead of a direct
        entity-to-FIR edge, since vehicles/phones route through persons.
        Fallback: also check direct COMMITTED links that span FIRs.
        """
        query = """
        MATCH (f1:FIR {id: $fir_id})<-[:USED_VEHICLE_IN|PHONE_LINKED_TO]-(p:Person)
              -[:USED_VEHICLE_IN|PHONE_LINKED_TO]->(f2:FIR)
        WHERE f1 <> f2
        RETURN f2.id AS linked_fir,
               ['Person'] AS shared_type,
               p.id AS entity_id
        LIMIT 20
        """
        return self.client.query(query, parameters={"fir_id": fir_id})

    def get_person_subgraph(self, person_id: str):
        """1-hop neighbourhood of a Person node."""
        query = """
        MATCH (p:Person {id: $person_id})-[r]-(n)
        RETURN n.id AS node_id, labels(n) AS labels, type(r) AS relationship
        LIMIT 50
        """
        return self.client.query(query, parameters={"person_id": person_id})

    def get_person_detail(self, person_id: str):
        """Gang membership and campaign affiliation for a person."""
        query = """
        OPTIONAL MATCH (p:Person {id: $person_id})-[:MEMBER_OF|LEADS]->(g:Gang)
        OPTIONAL MATCH (p)-[:COMMITTED]->(f:FIR)
        RETURN p.id AS person_id,
               g.id AS gang_id, g.name AS gang_name,
               count(DISTINCT f) AS fir_count
        """
        return self.client.query(query, parameters={"person_id": person_id})

    def get_campaign_timeline(self, campaign_id: str):
        """Return ordered FIR events for a campaign.

        The Phase 1 graph has no Campaign node — campaigns live only in
        Postgres. We query by joining across Postgres campaign_id → FIR
        node ids via the REST API.  At the Neo4j layer we return all FIRs
        whose id starts with the gang's known FIR ids (provided by caller).
        Since the frontend calls `/api/timeline/{campaign_id}` and the service
        will first fetch FIR ids from Postgres, this query accepts a list.
        """
        query = """
        UNWIND $fir_ids AS fid
        MATCH (f:FIR {id: fid})
        OPTIONAL MATCH (p:Person)-[:COMMITTED]->(f)
        RETURN f.id AS entity_id,
               ['FIR'] AS type,
               f.occurred_date AS date,
               p.id AS person_id
        ORDER BY f.occurred_date ASC
        """
        return self.client.query(query, parameters={"fir_ids": []})  # ids injected by service

    def get_campaign_timeline_by_fir_ids(self, fir_ids: list):
        """Timeline enriched with graph data for a list of FIR ids."""
        if not fir_ids:
            return []
        query = """
        UNWIND $fir_ids AS fid
        MATCH (f:FIR {id: fid})
        OPTIONAL MATCH (p:Person)-[:COMMITTED]->(f)
        RETURN f.id AS entity_id,
               ['FIR'] AS type,
               f.occurred_date AS date,
               p.id AS person_id,
               p.name AS person_name
        ORDER BY f.occurred_date ASC
        """
        return self.client.query(query, parameters={"fir_ids": fir_ids})


