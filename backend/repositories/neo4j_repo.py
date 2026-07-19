from backend.neo4j_client import neo4j_client

class Neo4jRepository:
    def __init__(self):
        self.client = neo4j_client

    def run_query(self, query: str, parameters: dict = None):
        return self.client.query(query, parameters)

    def get_campaigns(self):
        # A "campaign" = a gang led by a mastermind (Person)-[:LEADS]->(Gang),
        # scored by the total FIRs committed by the leader plus all gang members.
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
        query = """
        MATCH (f1:FIR {id: $fir_id})-[:INVOLVES]->(e)-[:INVOLVES]->(f2:FIR)
        WHERE f1 <> f2 AND (e:Phone OR e:Vehicle)
        RETURN f2.id AS linked_fir, labels(e) AS shared_type, e.id AS entity_id
        """
        return self.client.query(query, parameters={"fir_id": fir_id})

    def get_person_subgraph(self, person_id: str):
        query = """
        MATCH (p:Person {id: $person_id})-[r]-(n)
        RETURN n.id AS node_id, labels(n) AS labels, type(r) AS relationship
        """
        return self.client.query(query, parameters={"person_id": person_id})

    def get_campaign_timeline(self, campaign_id: str):
        query = """
        MATCH (c:Campaign {id: $campaign_id})<-[:BELONGS_TO]-(e)
        RETURN e.id AS entity_id, labels(e) AS type, e.date AS date
        ORDER BY e.date ASC
        """
        return self.client.query(query, parameters={"campaign_id": campaign_id})
