from __future__ import annotations
import numpy as np
from datetime import timedelta, datetime
from typing import List, Tuple, Dict

from simulator.geography.karnataka import Station
from simulator.schemas.crimes import CrimeEvent
from simulator.schemas.population import Vehicle, Phone, Citizen
from simulator.schemas.sensors import (
    CellTower, CCTVCamera, ANPRCamera,
    CellTowerPing, VehicleGPS, CCTVLog, ANPRLog
)

def build_sensor_networks(
    stations: List[Station],
    rng: np.random.Generator
) -> Tuple[List[CellTower], List[CCTVCamera], List[ANPRCamera]]:
    towers: List[CellTower] = []
    cctvs: List[CCTVCamera] = []
    anprs: List[ANPRCamera] = []
    
    t_idx = 0
    c_idx = 0
    a_idx = 0
    
    for station in stations:
        # Towers
        for _ in range(rng.integers(3, 8)):
            towers.append(CellTower(
                tower_id=f"TOW-{t_idx:05d}",
                latitude=round(station.latitude + rng.uniform(-0.04, 0.04), 5),
                longitude=round(station.longitude + rng.uniform(-0.04, 0.04), 5),
                district_id=station.district_id,
                station_id=station.station_id,
                provider=rng.choice(["Airtel", "Jio", "Vi", "BSNL"])
            ))
            t_idx += 1
            
        # CCTVs
        for _ in range(rng.integers(10, 30)):
            cctvs.append(CCTVCamera(
                camera_id=f"CAM-{c_idx:06d}",
                latitude=round(station.latitude + rng.uniform(-0.03, 0.03), 5),
                longitude=round(station.longitude + rng.uniform(-0.03, 0.03), 5),
                district_id=station.district_id,
                station_id=station.station_id,
                camera_type=rng.choice(["PUBLIC", "PRIVATE", "TRAFFIC"]),
                resolution=rng.choice(["720p", "1080p", "4K"])
            ))
            c_idx += 1
            
        # ANPRs
        for _ in range(rng.integers(1, 4)):
            anprs.append(ANPRCamera(
                anpr_id=f"ANPR-{a_idx:04d}",
                latitude=round(station.latitude + rng.uniform(-0.05, 0.05), 5),
                longitude=round(station.longitude + rng.uniform(-0.05, 0.05), 5),
                district_id=station.district_id,
                station_id=station.station_id
            ))
            a_idx += 1
            
    return towers, cctvs, anprs

def generate_sensor_traces(
    crime_events: List[CrimeEvent],
    towers: List[CellTower],
    cctvs: List[CCTVCamera],
    anprs: List[ANPRCamera],
    vehicles: List[Vehicle],
    rng: np.random.Generator
) -> Tuple[List[CellTowerPing], List[VehicleGPS], List[CCTVLog], List[ANPRLog]]:
    
    pings: List[CellTowerPing] = []
    gps: List[VehicleGPS] = []
    cctv_logs: List[CCTVLog] = []
    anpr_logs: List[ANPRLog] = []
    
    p_idx = 0
    g_idx = 0
    cl_idx = 0
    al_idx = 0
    
    # We map vehicle_id to Vehicle to get license plate for ANPR
    v_map = {v.vehicle_id: v for v in vehicles}
    
    # Fast spatial lookup approximations (using station_id mapping)
    towers_by_st = {s: [] for s in set(t.station_id for t in towers)}
    for t in towers: towers_by_st[t.station_id].append(t)
        
    cctv_by_st = {s: [] for s in set(c.station_id for c in cctvs)}
    for c in cctvs: cctv_by_st[c.station_id].append(c)
        
    anpr_by_st = {s: [] for s in set(a.station_id for a in anprs)}
    for a in anprs: anpr_by_st[a.station_id].append(a)
    
    for event in crime_events:
        if not event.primary_criminal_id: continue
        
        # Base timestamp for the crime
        crime_dt = datetime.combine(event.occurred_date, event.occurred_time)
        
        # Path: Start (T-60m) -> Scene (T) -> End (T+60m)
        path_lats = [event.latitude + rng.uniform(-0.05, 0.05), event.latitude, event.latitude + rng.uniform(-0.05, 0.05)]
        path_lngs = [event.longitude + rng.uniform(-0.05, 0.05), event.longitude, event.longitude + rng.uniform(-0.05, 0.05)]
        
        # Phone pings (every 15 mins for 2 hours)
        active_phones = event.phone_ids_involved
        for phone_id in active_phones:
            for m in range(-60, 61, 15):
                dt = crime_dt + timedelta(minutes=m)
                
                # interpolate position
                if m < 0:
                    fraction = (m + 60) / 60
                    lat = path_lats[0] + fraction * (path_lats[1] - path_lats[0])
                    lng = path_lngs[0] + fraction * (path_lngs[1] - path_lngs[0])
                else:
                    fraction = m / 60
                    lat = path_lats[1] + fraction * (path_lats[2] - path_lats[1])
                    lng = path_lngs[1] + fraction * (path_lngs[2] - path_lngs[1])
                    
                local_towers = towers_by_st.get(event.station_id, [])
                if not local_towers: continue
                # pick closest tower roughly
                tower = min(local_towers, key=lambda t: (t.latitude - lat)**2 + (t.longitude - lng)**2)
                
                pings.append(CellTowerPing(
                    ping_id=f"PING-{p_idx:08d}",
                    phone_id=phone_id,
                    tower_id=tower.tower_id,
                    timestamp=dt,
                    signal_strength=int(rng.integers(-100, -50))
                ))
                p_idx += 1
                
        # Vehicle GPS, CCTV, ANPR
        active_vehicles = event.vehicle_ids_involved
        for vehicle_id in active_vehicles:
            plate = v_map[vehicle_id].license_plate if vehicle_id in v_map else "UNKNOWN"
            # 5 minute intervals for GPS
            for m in range(-60, 61, 5):
                dt = crime_dt + timedelta(minutes=m)
                
                if m < 0:
                    fraction = (m + 60) / 60
                    lat = path_lats[0] + fraction * (path_lats[1] - path_lats[0])
                    lng = path_lngs[0] + fraction * (path_lngs[1] - path_lngs[0])
                else:
                    fraction = m / 60
                    lat = path_lats[1] + fraction * (path_lats[2] - path_lats[1])
                    lng = path_lngs[1] + fraction * (path_lngs[2] - path_lngs[1])
                    
                # Vehicle GPS
                gps.append(VehicleGPS(
                    gps_id=f"VGPS-{g_idx:08d}",
                    vehicle_id=vehicle_id,
                    latitude=lat,
                    longitude=lng,
                    timestamp=dt,
                    speed_kmh=round(rng.uniform(10, 60), 1)
                ))
                g_idx += 1
                
                # Check CCTV proximity
                local_cctvs = cctv_by_st.get(event.station_id, [])
                for cam in local_cctvs:
                    if (cam.latitude - lat)**2 + (cam.longitude - lng)**2 < 0.0001:
                        cctv_logs.append(CCTVLog(
                            log_id=f"CLOG-{cl_idx:08d}",
                            camera_id=cam.camera_id,
                            timestamp=dt,
                            vehicle_id=vehicle_id,
                            person_id=event.primary_criminal_id,
                            confidence=round(rng.uniform(0.4, 0.95), 2)
                        ))
                        cl_idx += 1
                        
                # Check ANPR proximity
                local_anprs = anpr_by_st.get(event.station_id, [])
                for cam in local_anprs:
                    if (cam.latitude - lat)**2 + (cam.longitude - lng)**2 < 0.0002:
                        read = plate
                        if rng.random() < 0.1: # OCR error
                            read = read[:-1] + rng.choice(["A", "B", "1"])
                        anpr_logs.append(ANPRLog(
                            log_id=f"ALOG-{al_idx:08d}",
                            anpr_id=cam.anpr_id,
                            vehicle_id=vehicle_id,
                            plate_read=read,
                            timestamp=dt,
                            speed_kmh=round(rng.uniform(20, 80), 1)
                        ))
                        al_idx += 1
                        
    return pings, gps, cctv_logs, anpr_logs
