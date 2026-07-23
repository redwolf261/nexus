import os
import sys

# Ensure DATABASE_URL points to file-backed SQLite database for shared session tables in tests
os.environ["DATABASE_URL"] = "sqlite:///./test_runner.db"
os.environ["TESTING"] = "1"

import pytest
from backend.database import Base, engine
import backend.db.schema
import backend.events.event_models

@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_runner.db"):
        try:
            os.remove("./test_runner.db")
        except Exception:
            pass
