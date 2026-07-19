from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models import FIR, Person, Vehicle

class PostgresRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_firs(self, limit: int = 50) -> List[FIR]:
        return self.db.query(FIR).limit(limit).all()

    def get_fir_by_id(self, fir_id: str) -> Optional[FIR]:
        return self.db.query(FIR).filter(FIR.fir_id == fir_id).first()

    def get_person_by_id(self, citizen_id: str) -> Optional[Person]:
        return self.db.query(Person).filter(Person.citizen_id == citizen_id).first()
