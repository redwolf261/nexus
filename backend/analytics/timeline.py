def format_timeline_events(raw_events):
    """
    Transforms raw neo4j temporal events into an ordered timeline.
    """
    timeline = []
    for idx, row in enumerate(raw_events):
        timeline.append({
            "day": idx + 1,
            "event_type": row["type"][0] if row["type"] else "Event",
            "entity_id": row["entity_id"],
            "description": f"Occurred on {row['date']}"
        })
    return timeline
