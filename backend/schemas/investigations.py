from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class InvestigationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    status: str = Field("Open", max_length=50)
    priority: str = Field("Medium", max_length=50)
    assigned_officer: Optional[str] = Field(None, max_length=100)

class InvestigationCreate(InvestigationBase):
    pass

class InvestigationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=50)
    assigned_officer: Optional[str] = Field(None, max_length=100)
    version: int = Field(..., description="Current version of the investigation for optimistic concurrency")

class InvestigationResponse(InvestigationBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    version: int
    last_sequence: int

    class Config:
        from_attributes = True

class InvestigationEntityResponse(BaseModel):
    investigation_id: str
    entity_type: str
    entity_id: str
    added_at: datetime

    class Config:
        from_attributes = True

from pydantic import field_validator
import bleach

class InvestigationNoteCreate(BaseModel):
    markdown: str = Field(..., max_length=50000)

    @field_validator("markdown")
    @classmethod
    def sanitize_markdown(cls, v: str) -> str:
        return bleach.clean(v)

class InvestigationNoteUpdate(BaseModel):
    markdown: str = Field(..., max_length=50000)
    version: int = Field(..., description="Current version of the note for optimistic concurrency")

    @field_validator("markdown")
    @classmethod
    def sanitize_markdown(cls, v: str) -> str:
        return bleach.clean(v)

class InvestigationNoteResponse(BaseModel):
    id: str
    investigation_id: str
    author: Optional[str] = None
    markdown: str
    created_at: datetime
    updated_at: datetime
    version: int

    class Config:
        from_attributes = True

class InvestigationActivityResponse(BaseModel):
    id: int
    investigation_id: str
    action: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Workspace schemas
class TimelineEvent(BaseModel):
    date: datetime
    type: str
    event_type: str
    description: str
    entity_id: Optional[str] = None

class InvestigationWorkspaceResponse(BaseModel):
    investigation: InvestigationResponse
    entities: dict # Map of type to list of details
    notes: List[InvestigationNoteResponse]
    timeline: List[TimelineEvent]
    statistics: dict
