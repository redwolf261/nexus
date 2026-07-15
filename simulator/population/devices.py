"""
NEXUS Simulator — Device Generators
Generates canonical Vehicle and Phone entities for citizens and criminals.
"""
from __future__ import annotations
import numpy as np
from typing import List, Tuple

from simulator.schemas.population import Citizen, Vehicle, Phone
from simulator.criminals.profiles import CriminalProfile

VEHICLE_MAKES = ["Maruti Suzuki", "Hyundai", "Tata", "Mahindra", "Honda", "Toyota", "Hero", "TVS", "Bajaj", "Royal Enfield"]
VEHICLE_COLORS = ["white", "black", "silver", "red", "blue", "grey"]
PHONE_PROVIDERS = ["Jio", "Airtel", "Vi", "BSNL"]

def generate_devices(
    citizens: List[Citizen],
    criminals: List[CriminalProfile],
    rng: np.random.Generator,
    current_year: int
) -> Tuple[List[Vehicle], List[Phone]]:
    
    vehicles: List[Vehicle] = []
    phones: List[Phone] = []
    
    # 1. Generate devices for citizens
    for citizen in citizens:
        if citizen.is_adult and rng.random() < 0.85:
            # Generate phone
            phone_id = f"PHN-{len(phones):08d}"
            phones.append(Phone(
                phone_id=phone_id,
                owner_id=citizen.citizen_id,
                phone_number=citizen.phone_primary,
                provider=rng.choice(PHONE_PROVIDERS),
                type=rng.choice(["smartphone", "feature_phone"], p=[0.8, 0.2]),
                is_burner=False,
            ))
            
        if citizen.has_vehicle_license and rng.random() < 0.60:
            # Generate vehicle
            v_id = f"VEH-{len(vehicles):08d}"
            v_type = rng.choice(["car", "motorcycle", "scooter"], p=[0.4, 0.4, 0.2])
            is_two_wheeler = v_type in {"motorcycle", "scooter"}
            
            if is_two_wheeler:
                make = rng.choice(["Hero", "TVS", "Bajaj", "Royal Enfield", "Honda"])
            else:
                make = rng.choice(["Maruti Suzuki", "Hyundai", "Tata", "Mahindra", "Honda", "Toyota"])
                
            vehicles.append(Vehicle(
                vehicle_id=v_id,
                owner_id=citizen.citizen_id,
                license_plate=f"KA {rng.integers(1, 50+1):02d} {rng.choice(['A','B','C','M','N','P'])} {rng.integers(1000, 9999+1)}",
                make=make,
                model="Model X",
                color=rng.choice(VEHICLE_COLORS),
                type=v_type,
                registration_year=int(rng.integers(current_year - 15, current_year + 1)),
                is_stolen=False,
            ))
            
    # 2. Map generated devices to criminals and create burners
    # Criminals also need access to devices. If they are citizens, they already have canonical devices.
    # We will assign the canonical device IDs back to the CriminalProfile
    
    citizen_to_vehicle = {v.owner_id: v.vehicle_id for v in vehicles}
    citizen_to_phone = {p.owner_id: p.phone_id for p in phones}
    
    for c in criminals:
        c.vehicle_ids = []
        c.phone_ids = []
        
        # Link their legitimate citizen devices
        if c.citizen_id in citizen_to_vehicle:
            c.vehicle_ids.append(citizen_to_vehicle[c.citizen_id])
        if c.citizen_id in citizen_to_phone:
            c.phone_ids.append(citizen_to_phone[c.citizen_id])
            
        # Criminals (especially gangs) might have burners or stolen vehicles
        if rng.random() < 0.3:
            b_id = f"PHN-{len(phones):08d}"
            phones.append(Phone(
                phone_id=b_id,
                owner_id=c.citizen_id,
                phone_number=f"9{rng.integers(100000000, 999999999)}",
                provider=rng.choice(PHONE_PROVIDERS),
                type="feature_phone",
                is_burner=True,
            ))
            c.phone_ids.append(b_id)
            
        if c.is_gang_member and rng.random() < 0.5:
            # Gangs might have unregistered/stolen vehicles they share
            v_id = f"VEH-{len(vehicles):08d}"
            vehicles.append(Vehicle(
                vehicle_id=v_id,
                owner_id=c.gang_id, # Owner is the gang essentially
                license_plate=f"KA {rng.integers(1, 50+1):02d} FAKE {rng.integers(1000, 9999+1)}",
                make="Mahindra",
                model="Scorpio",
                color="black",
                type="car",
                registration_year=current_year - 5,
                is_stolen=True,
            ))
            c.vehicle_ids.append(v_id)

    return vehicles, phones
