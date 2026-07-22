from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid

from backend.db.schema import Investigation, InvestigationEntity, InvestigationNote, InvestigationActivity, InvestigationCollaborator

class InvestigationsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_investigations(self, status: str = None, skip: int = 0, limit: int = 50) -> List[Investigation]:
        q = self.db.query(Investigation)
        if status:
            q = q.filter(Investigation.status == status)
        return q.order_by(Investigation.updated_at.desc()).offset(skip).limit(limit).all()

    def get_investigation(self, inv_id: str) -> Optional[Investigation]:
        return self.db.query(Investigation).filter(Investigation.id == inv_id).first()

    def create_investigation(self, data: dict, created_by: str = "system") -> Investigation:
        inv_id = "INV-" + str(uuid.uuid4())[:8].upper()
        inv = Investigation(id=inv_id, created_by=created_by, **data)
        self.db.add(inv)
        self._log_activity(inv_id, "CREATED", f"Investigation {inv.title} created")
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def update_investigation(self, inv_id: str, data: dict) -> Optional[Investigation]:
        inv = self.get_investigation(inv_id)
        if not inv: return None
        
        expected_version = data.pop('version', None)
        if expected_version is not None and inv.version != expected_version:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail=f"Conflict: Investigation has been modified (expected {expected_version}, got {inv.version})")
            
        for k, v in data.items():
            if v is not None:
                setattr(inv, k, v)
                self._log_activity(inv_id, "UPDATED", f"Field {k} updated")
        inv.version += 1
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def add_entity(self, inv_id: str, entity_type: str, entity_id: str):
        existing = self.db.query(InvestigationEntity).filter_by(
            investigation_id=inv_id, entity_type=entity_type, entity_id=entity_id
        ).first()
        if not existing:
            ent = InvestigationEntity(investigation_id=inv_id, entity_type=entity_type, entity_id=entity_id)
            self.db.add(ent)
            self._log_activity(inv_id, "ENTITY_ADDED", f"Added {entity_type} {entity_id}")
            self.db.commit()

    def remove_entity(self, inv_id: str, entity_type: str, entity_id: str):
        ent = self.db.query(InvestigationEntity).filter_by(
            investigation_id=inv_id, entity_type=entity_type, entity_id=entity_id
        ).first()
        if ent:
            self.db.delete(ent)
            self._log_activity(inv_id, "ENTITY_REMOVED", f"Removed {entity_type} {entity_id}")
            self.db.commit()

    def get_entities(self, inv_id: str) -> List[InvestigationEntity]:
        return self.db.query(InvestigationEntity).filter_by(investigation_id=inv_id).all()

    def add_note(self, inv_id: str, markdown: str, author: str = "system") -> InvestigationNote:
        note_id = "NOTE-" + str(uuid.uuid4())[:8].upper()
        note = InvestigationNote(id=note_id, investigation_id=inv_id, markdown=markdown, author=author)
        self.db.add(note)
        self._log_activity(inv_id, "NOTE_ADDED", "Note added")
        self.db.commit()
        self.db.refresh(note)
        return note

    def update_note(self, note_id: str, markdown: str, version: int = None) -> Optional[InvestigationNote]:
        note = self.db.query(InvestigationNote).filter_by(id=note_id).first()
        if note:
            if version is not None and note.version != version:
                from fastapi import HTTPException
                raise HTTPException(status_code=409, detail=f"Conflict: Note has been modified (expected {version}, got {note.version})")
            note.markdown = markdown
            note.version += 1
            self._log_activity(note.investigation_id, "NOTE_UPDATED", "Note updated")
            self.db.commit()
            self.db.refresh(note)
        return note

    def get_notes(self, inv_id: str) -> List[InvestigationNote]:
        return self.db.query(InvestigationNote).filter_by(investigation_id=inv_id).order_by(InvestigationNote.created_at.desc()).all()

    def get_activity(self, inv_id: str) -> List[InvestigationActivity]:
        return self.db.query(InvestigationActivity).filter_by(investigation_id=inv_id).order_by(InvestigationActivity.created_at.desc()).all()

    def _log_activity(self, inv_id: str, action: str, details: str):
        act = InvestigationActivity(investigation_id=inv_id, action=action, details=details)
        self.db.add(act)

    def is_collaborator(self, inv_id: str, user_id: str) -> bool:
        return self.db.query(InvestigationCollaborator).filter_by(investigation_id=inv_id, user_id=user_id).first() is not None

    def add_collaborator(self, inv_id: str, user_id: str):
        if not self.is_collaborator(inv_id, user_id):
            collab = InvestigationCollaborator(investigation_id=inv_id, user_id=user_id)
            self.db.add(collab)
            self._log_activity(inv_id, 'COLLABORATOR_ADDED', f'Added user {user_id}')
            self.db.commit()
