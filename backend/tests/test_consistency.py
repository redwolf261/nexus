import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.repositories.investigations_repo import InvestigationsRepository

client = TestClient(app)

def test_optimistic_concurrency(mocker):
    # Setup test data
    db = SessionLocal()
    repo = InvestigationsRepository(db)
    
    # Create investigation
    inv = repo.create_investigation({"title": "Concurrency Test", "status": "Open", "priority": "High"})
    inv_id = inv.id
    
    # Get current version
    current_version = inv.version
    
    # Attempt to update with incorrect version (e.g. simulated conflict)
    # The endpoint needs auth, so we'll mock auth
    mocker.patch("backend.api.routers.investigations.get_current_user", return_value={"id": "SYSTEM", "role": "Admin"})
    mocker.patch("backend.api.routers.investigations.require_role", return_value=lambda: {"id": "SYSTEM", "role": "Admin"})
    mocker.patch("backend.api.routers.investigations.require_ownership_or_admin", return_value=True)
    
    # Just test the repo directly for optimistic concurrency since router testing requires full auth mock
    try:
        from fastapi import HTTPException
        repo.update_investigation(inv_id, {"title": "Conflict Title", "version": current_version - 1})
        assert False, "Should have raised HTTPException for conflict"
    except HTTPException as e:
        assert e.status_code == 409
        
    # Attempt to update with correct version
    updated_inv = repo.update_investigation(inv_id, {"title": "Updated Title", "version": current_version})
    assert updated_inv.version == current_version + 1
    assert updated_inv.title == "Updated Title"
    db.close()

def test_idempotent_entity_attachment():
    db = SessionLocal()
    repo = InvestigationsRepository(db)
    inv = repo.create_investigation({"title": "Idempotent Test", "status": "Open", "priority": "High"})
    
    # Add entity twice
    repo.add_entity(inv.id, "person", "PERSON-001")
    repo.add_entity(inv.id, "person", "PERSON-001")
    
    entities = repo.get_entities(inv.id)
    person_entities = [e for e in entities if e.entity_id == "PERSON-001"]
    
    # Should only exist once
    assert len(person_entities) == 1
    db.close()

def test_event_sequence_generation():
    db = SessionLocal()
    repo = InvestigationsRepository(db)
    inv = repo.create_investigation({"title": "Seq Test", "status": "Open", "priority": "High"})
    
    from backend.events.event_models import BaseEvent
    from backend.events.event_types import EventType
    from backend.events.dispatcher import EventDispatcher
    import asyncio
    
    event = BaseEvent(event_type=EventType.NOTE_ADDED, payload={"msg": "test"}, case_id=inv.id)
    
    # We must run asyncio for the publish method
    loop = asyncio.get_event_loop()
    loop.run_until_complete(EventDispatcher.publish(event, db))
    
    assert event.sequence == 1
    
    event2 = BaseEvent(event_type=EventType.NOTE_ADDED, payload={"msg": "test2"}, case_id=inv.id)
    loop.run_until_complete(EventDispatcher.publish(event2, db))
    
    assert event2.sequence == 2
    db.close()
