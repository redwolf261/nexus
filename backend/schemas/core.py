from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class PersonBase(BaseModel):
    citizen_id: str
    name_en: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone_primary: Optional[str] = None
    occupation: Optional[str] = None
    district_name: Optional[str] = None
    is_migrant: Optional[bool] = None

class PersonResponse(PersonBase):
    model_config = ConfigDict(from_attributes=True)

class FIRBase(BaseModel):
    fir_id: str
    fir_number: Optional[str] = None
    station_id: Optional[str] = None
    district_name: Optional[str] = None
    occurred_date: Optional[date] = None
    crime_type: Optional[str] = None
    crime_category: Optional[str] = None
    status: Optional[str] = None
    description_en: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FIRResponse(FIRBase):
    model_config = ConfigDict(from_attributes=True)
