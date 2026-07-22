# NEXUS Platform Architecture

## System Overview

```mermaid
graph TD
    subgraph Data Layer
        PG[(PostgreSQL)]
        N4J[(Neo4j)]
    end

    subgraph Backend
        API[FastAPI Service]
        Auth[Auth Middleware]
        Log[Structured Logging]
        API --> PG
        API --> N4J
        API --> Auth
        API --> Log
    end

    subgraph Frontend
        Next[Next.js App]
        RQ[React Query]
        Next --> RQ
        RQ --> API
    end

    subgraph External
        Simulator[Data Simulator]
        Simulator -.-> |Batch Load| PG
        Simulator -.-> |Batch Load| N4J
    end
```

## Relational Entity-Relationship (Postgres)

```mermaid
erDiagram
    PERSON ||--o{ FIR : "committed"
    PERSON ||--o{ VEHICLE : "owns"
    PERSON ||--o{ PHONE : "owns"
    PERSON ||--o| CRIMINAL : "has_record"
    
    FIR ||--o{ ACCUSED : "has"
    FIR ||--o{ VICTIM : "has"
    FIR ||--o{ EVIDENCE : "has"
    
    GANG ||--o{ CRIMINAL : "members"
    GANG ||--o{ CAMPAIGN : "executes"
    CAMPAIGN ||--o{ FIR : "contains"
    
    INVESTIGATION ||--o{ INVESTIGATION_ENTITY : "tracks"
    INVESTIGATION ||--o{ INVESTIGATION_NOTE : "has"
    INVESTIGATION ||--o{ INVESTIGATION_ACTIVITY : "logs"
```

## Graph Schema (Neo4j)

```mermaid
graph LR
    P[Person] -- COMMITTED --> F[FIR]
    P -- USED_VEHICLE_IN --> F
    P -- PHONE_LINKED_TO --> F
    P -- MEMBER_OF --> G[Gang]
    P -- LEADS --> G
    P -- KNOWS --> P
```

## Data Consistency Model
PostgreSQL acts as the single source of truth for entity attributes and primary keys. Neo4j acts as the topological index.
- All entities (Person, Vehicle, FIR) map 1:1 between Postgres and Neo4j using the same `id` strings.
- Frontend fetches relationship structure from Neo4j (e.g. Silo Buster) and enriches it with Postgres data (e.g. `useFIRDetail`).
