from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Text
from backend.database import Base

class Person(Base):
    __tablename__ = "persons"

    citizen_id = Column(String, primary_key=True, index=True)
    name_en = Column(String, index=True)
    gender = Column(String)
    age = Column(Integer)
    phone_primary = Column(String, index=True)
    occupation = Column(String)
    home_address = Column(String)
    district_name = Column(String)
    is_migrant = Column(Boolean)

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, index=True)
    license_plate = Column(String, index=True)
    make = Column(String)
    model = Column(String)
    color = Column(String)
    is_stolen = Column(Boolean)

class FIR(Base):
    __tablename__ = "firs"

    fir_id = Column(String, primary_key=True, index=True)
    fir_number = Column(String, index=True)
    station_id = Column(String, index=True)
    district_name = Column(String)
    occurred_date = Column(Date, index=True)
    crime_type = Column(String)
    crime_category = Column(String, index=True)
    status = Column(String)
    description_en = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
