import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "nexus_password")

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

# Global instance for the app
neo4j_client = Neo4jClient(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
