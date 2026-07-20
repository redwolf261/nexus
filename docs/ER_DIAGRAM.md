# NEXUS Relational Schema — Entity Relationships

Postgres schema defined in [`backend/db/schema.py`](../backend/db/schema.py).
32 hard foreign keys are enforced by the database; circular and polymorphic
references are soft (indexed, validated) — see [MIGRATION_PLAN.md](MIGRATION_PLAN.md).

## Core entity-relationship diagram

```mermaid
erDiagram
    districts   ||--o{ stations         : has
    districts   ||--o{ officers         : staffs
    districts   ||--o{ persons          : resides
    districts   ||--o{ pois             : locates
    districts   ||--o{ firs             : jurisdiction
    stations    ||--o{ officers         : posts
    stations    ||--o{ firs             : registers

    persons     ||--o{ vehicles         : owns
    persons     ||--o{ phones           : owns
    persons     ||--o| criminals        : "flagged as"

    gangs       ||--o{ campaigns        : runs
    districts   ||--o{ campaigns        : targets
    gangs       ||--o{ gang_members     : includes
    criminals   ||--o{ gang_members     : "member of"
    criminals   ||--o{ criminal_associates : "associates"

    firs        ||--o{ victims          : names
    firs        ||--o{ accused          : names
    firs        ||--o{ evidence         : yields
    firs        ||--o{ investigation_logs : tracks
    firs        ||--o{ chargesheets     : produces
    firs        ||--o{ arrests          : leads_to
    firs        ||--o{ court_cases      : escalates
    firs        ||--o{ fir_accomplices  : links
    firs        ||--o{ fir_vehicles     : links
    firs        ||--o{ fir_phones       : links
    criminals   ||--o{ fir_accomplices  : "named in"
    vehicles    ||--o{ fir_vehicles     : "seen in"
    phones      ||--o{ fir_phones       : "seen in"
```

## Soft references (no DB-enforced FK)

| From | To | Why soft |
|---|---|---|
| criminals.gang_id | gangs.gang_id | Reference cycle with gangs.leader_criminal_id |
| gangs.leader_criminal_id | criminals.criminal_id | Reference cycle with criminals.gang_id |
| social_network (source/target) | persons / criminals | Polymorphic — endpoints span entity types |
| entity_resolution (ids) | multiple | Polymorphic match candidates |
| telemetry (cctv/anpr/cdr/gps/pings) | cameras / phones / vehicles | High-volume; integrity checked, not constrained |

Both cycle directions and all polymorphic edges are indexed for join performance and
verified by the validation pipeline (`check_fk_integrity` covers hard FKs;
soft refs are checked structurally).

## Fact table

`firs` is the central fact table — 1,000 rows fanning out to victims, accused,
evidence, investigation logs, chargesheets, arrests, court cases, and the three
FIR junction tables. Most analytical queries anchor here.
