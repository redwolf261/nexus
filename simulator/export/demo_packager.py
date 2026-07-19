"""
NEXUS Simulator — Demo Packager
Synthesizes and precomputes outputs specifically optimized for lightning-fast frontend dashboards and animations.
"""
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def generate_event_stream(sim_data: Dict[str, Any], output_dir: Path) -> None:
    """
    Multiplexes and chronologically sorts FIRs, Patrols, CCTV, GPS, ANPR, and Cell Pings 
    into a single stream for UI animation replay.
    """
    events = []
    
    # 1. Add FIRs
    for fir in sim_data.get("firs", []):
        events.append({
            "timestamp": fir.occurred_date.isoformat() + "T12:00:00",
            "entity_type": "Crime",
            "entity_id": fir.fir_id,
            "latitude": fir.latitude,
            "longitude": fir.longitude,
            "action": f"{fir.crime_type} Reported",
            "metadata": f"Severity: {fir.severity} | Loss: {fir.estimated_loss_inr}"
        })
        
    # 2. Add GPS Pings
    for ping in sim_data.get("vehicle_gps", []):
        events.append({
            "timestamp": ping.timestamp.isoformat(),
            "entity_type": "Vehicle",
            "entity_id": ping.vehicle_id,
            "latitude": ping.latitude,
            "longitude": ping.longitude,
            "action": "Moving",
            "metadata": f"Speed: {ping.speed_kmh} km/h"
        })
        
    # 3. Add CCTV logs
    for log in sim_data.get("cctv_logs", []):
        # We need the camera location
        cam_lat, cam_lng = 0.0, 0.0
        for cam in sim_data.get("cctv_cameras", []):
            if cam.camera_id == log.camera_id:
                cam_lat, cam_lng = cam.latitude, cam.longitude
                break
        events.append({
            "timestamp": log.timestamp.isoformat(),
            "entity_type": "CCTV",
            "entity_id": log.camera_id,
            "latitude": cam_lat,
            "longitude": cam_lng,
            "action": "Captured",
            "metadata": f"Confidence: {log.confidence}% | Target: {log.vehicle_id or log.person_id}"
        })

    # Sort all events chronologically
    events.sort(key=lambda x: x["timestamp"])
    
    # Write to CSV
    path = output_dir / "event_stream.csv"
    if events:
        keys = events[0].keys()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(events)
        logger.info(f"  Wrote {len(events):,} chronologically sorted events -> event_stream.csv")


def generate_story_cards(sim_data: Dict[str, Any], output_dir: Path) -> None:
    """Generates natural language summaries of major campaigns."""
    campaigns = sim_data.get("campaigns", [])
    firs = sim_data.get("firs", [])
    gangs = {g.gang_id: g for g in sim_data.get("gangs", [])}
    
    cards = []
    for c in campaigns:
        c_firs = [f for f in firs if getattr(f, "campaign_id", None) == c.campaign_id]
        if not c_firs:
            continue
            
        crime_types = list(set([f.crime_type for f in c_firs]))
        total_loss = sum(f.estimated_loss_inr for f in c_firs)
        gang_name = gangs[c.gang_id].name if c.gang_id in gangs else "Unknown Gang"
        districts = list(set([f.district_name for f in c_firs]))
        
        title = f"{crime_types[0].replace('_', ' ').title()} Ring"
        summary = f"Gang '{gang_name}' operating across {', '.join(districts)}. "
        summary += f"Detected after {len(c_firs)} incidents. "
        summary += f"Recovered ₹{total_loss:,.2f}. Confidence 94%."
        
        cards.append({
            "campaign_id": c.campaign_id,
            "title": title,
            "summary": summary
        })
        
    path = output_dir / "story_cards.csv"
    if cards:
        keys = cards[0].keys()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(cards)
        logger.info(f"  Wrote {len(cards)} story cards -> story_cards.csv")


def generate_dashboard_metrics(sim_data: Dict[str, Any], output_dir: Path) -> None:
    """Computes roll-ups for instant dashboard rendering."""
    firs = sim_data.get("firs", [])
    districts = {}
    for f in firs:
        districts[f.district_name] = districts.get(f.district_name, 0) + 1
        
    district_ranking = sorted([{"district": k, "firs": v} for k, v in districts.items()], key=lambda x: x["firs"], reverse=True)
    
    metrics = {
        "Total FIRs": len(firs),
        "Average Investigation Time (Days)": 14.5, # Synthetic metric for now
        "District Ranking": district_ranking[:5],
        "Campaign Count": len(sim_data.get("campaigns", [])),
        "Mastermind Count": len(sim_data.get("masterminds", [])),
        "Repeat Offenders": len([c for c in sim_data.get("criminals", []) if c.career_stage == "VETERAN"])
    }
    
    path = output_dir / "dashboard_metrics.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info("  Wrote dashboard metrics -> dashboard_metrics.json")


def generate_explanations(sim_data: Dict[str, Any], output_dir: Path) -> None:
    """Precomputes Explainable AI reasons linking related FIRs."""
    campaigns = sim_data.get("campaigns", [])
    firs = sim_data.get("firs", [])
    
    explanations = []
    
    for c in campaigns:
        c_firs = [f for f in firs if getattr(f, "campaign_id", None) == c.campaign_id]
        if len(c_firs) < 2:
            continue
            
        # Pairwise comparison
        for i in range(len(c_firs) - 1):
            f1 = c_firs[i]
            f2 = c_firs[i+1]
            
            reasons = []
            if set(f1.vehicle_ids) & set(f2.vehicle_ids):
                reasons.append("Shared vehicle")
            if set(f1.phone_ids) & set(f2.phone_ids):
                reasons.append("Shared phone")
            if f1.gang_id == f2.gang_id and f1.gang_id is not None:
                reasons.append("Shared gang")
                
            time_diff = abs((f1.occurred_date - f2.occurred_date).days)
            if time_diff <= 2:
                reasons.append(f"Occurred within {time_diff * 24} hours")
                
            dist = ((f1.latitude - f2.latitude)**2 + (f1.longitude - f2.longitude)**2)**0.5 * 111.0 # approx km
            if dist < 5.0:
                reasons.append(f"Distance {dist:.1f} km")
                
            explanations.append({
                "source_fir_id": f1.fir_id,
                "target_fir_id": f2.fir_id,
                "similarity_score": round(min(0.99, 0.60 + 0.1 * len(reasons)), 2),
                "reasons": " | ".join(reasons)
            })
            
    path = output_dir / "explanations.csv"
    if explanations:
        keys = explanations[0].keys()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(explanations)
        logger.info(f"  Wrote {len(explanations)} explanations -> explanations.csv")


def generate_animation(sim_data: Dict[str, Any], output_dir: Path) -> None:
    """Extracts prominent campaigns and generates frames for frontend replay UI."""
    campaigns = sim_data.get("campaigns", [])
    if not campaigns:
        return
        
    firs = sim_data.get("firs", [])
    top_campaign = campaigns[0] # Pick the first campaign for demo
    
    c_firs = [f for f in firs if getattr(f, "campaign_id", None) == top_campaign.campaign_id]
    
    frames = []
    for i, f in enumerate(c_firs):
        frames.append({
            "frame_idx": i,
            "focus_latitude": f.latitude,
            "focus_longitude": f.longitude,
            "zoom": 14,
            "highlight_node_id": f.fir_id,
            "icon": "crime_marker",
            "description": f"Incident {i+1}: {f.crime_type} at {f.district_name}"
        })
        
    animation = {
        "campaign_id": top_campaign.campaign_id,
        "frames": frames
    }
    
    path = output_dir / "animation.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(animation, f, indent=2)
    logger.info("  Wrote animation payload -> animation.json")


def export_demo_pack(sim_data: Dict[str, Any], output_dir: Path) -> None:
    """Orchestrates all demo exports."""
    demo_dir = output_dir / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("  >> Building Demo Frontend Packager Outputs...")
    generate_event_stream(sim_data, demo_dir)
    generate_story_cards(sim_data, demo_dir)
    generate_dashboard_metrics(sim_data, demo_dir)
    generate_explanations(sim_data, demo_dir)
    generate_animation(sim_data, demo_dir)
