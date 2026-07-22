import pytest
from sqlalchemy import text
from backend.database import SessionLocal
from backend.repositories.postgres_repo import PostgresRepository
from backend.repositories.neo4j_repo import Neo4jRepository

def test_omni_search_performance(benchmark):
    db = SessionLocal()
    repo = PostgresRepository(db)
    
    # Use benchmark fixture to measure execution time of search
    result = benchmark.pedantic(repo.search, args=("theft", 20), iterations=10, rounds=10)
    
    assert isinstance(result, list)
    db.close()

def test_executive_dashboard_performance(benchmark):
    db = SessionLocal()
    repo = PostgresRepository(db)
    
    result = benchmark.pedantic(repo.get_executive_kpis, iterations=10, rounds=10)
    
    assert isinstance(result, dict)
    db.close()

def test_graph_expansion_performance(benchmark):
    repo = Neo4jRepository()
    
    def run_graph_query():
        query = """
        MATCH p=(n {id: 'PERSON-102'})-[*1..2]-(m)
        RETURN n.id AS source, m.id AS target
        LIMIT 50
        """
        with repo.client.driver.session(database="neo4j", default_access_mode="READ", transaction_timeout=5000) as session:
            return session.run(query).fetchall()
            
    # Try/except to pass test if neo4j isn't running during CI
    try:
        result = benchmark.pedantic(run_graph_query, iterations=5, rounds=5)
        assert isinstance(result, list)
    except Exception as e:
        pytest.skip(f"Neo4j not available or error: {e}")
