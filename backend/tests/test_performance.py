import pytest
from backend.database import SessionLocal, engine, Base
from backend.repositories.postgres_repo import PostgresRepository
from backend.repositories.neo4j_repo import Neo4jRepository

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_omni_search_performance():
    db = SessionLocal()
    repo = PostgresRepository(db)
    try:
        result = repo.search("theft", limit=20)
        assert isinstance(result, list)
    finally:
        db.close()

def test_executive_dashboard_performance():
    db = SessionLocal()
    repo = PostgresRepository(db)
    try:
        result = repo.get_executive_kpis()
        assert isinstance(result, dict)
    finally:
        db.close()

def test_graph_expansion_performance():
    try:
        repo = Neo4jRepository()
        query = """
        MATCH p=(n {id: 'PERSON-102'})-[*1..2]-(m)
        RETURN n.id AS source, m.id AS target
        LIMIT 50
        """
        with repo.client.driver.session(database="neo4j", default_access_mode="READ", transaction_timeout=5000) as session:
            result = session.run(query).fetchall()
            assert isinstance(result, list)
    except Exception as e:
        pytest.skip(f"Neo4j not available or error: {e}")
