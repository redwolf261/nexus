import os
from backend.neo4j_client import neo4j_client

def load_graph():
    print("Initializing Neo4j Graph...")

    # Constraints for performance
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (f:FIR) REQUIRE f.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Gang) REQUIRE g.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.id IS UNIQUE"
    ]
    for q in constraints:
        neo4j_client.query(q)

    # In a real environment, we'd use neo4j-admin database import,
    # but for local dev with smaller datasets, we can use Cypher LOAD CSV if files are accessible.
    print("Graph initialization complete. For full data load, use 'neo4j-admin database import' with the output/neo4j/ nodes and relationships CSVs generated during simulation.")

if __name__ == "__main__":
    load_graph()
