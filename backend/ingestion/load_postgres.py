import os
import pandas as pd
from backend.database import engine, Base
from backend.models import Person, Vehicle, FIR

def load_data():
    print("Creating tables in PostgreSQL...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../output"))

    print("Loading Persons...")
    persons_df = pd.read_csv(f"{data_dir}/persons.csv")
    # For simplicity, taking a subset of columns mapping to our model
    persons_to_insert = persons_df[[
        "citizen_id", "name_en", "gender", "age", "phone_primary", 
        "occupation", "home_address", "district_name", "is_migrant"
    ]]
    persons_to_insert.to_sql("persons", engine, if_exists="append", index=False)

    print("Loading Vehicles...")
    vehicles_df = pd.read_csv(f"{data_dir}/vehicles.csv")
    vehicles_to_insert = vehicles_df[[
        "vehicle_id", "owner_id", "license_plate", "make", "model", "color", "is_stolen"
    ]]
    vehicles_to_insert.to_sql("vehicles", engine, if_exists="append", index=False)

    print("Loading FIRs...")
    firs_df = pd.read_csv(f"{data_dir}/firs.csv")
    # Convert date strings to actual dates/times if necessary, pandas will do fine
    firs_to_insert = firs_df[[
        "fir_id", "fir_number", "station_id", "district_name", "occurred_date", 
        "crime_type", "crime_category", "status", "description_en", "latitude", "longitude"
    ]]
    firs_to_insert.to_sql("firs", engine, if_exists="append", index=False)

    print("PostgreSQL Data Loading Complete.")

if __name__ == "__main__":
    load_data()
