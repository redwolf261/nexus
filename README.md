# NEXUS: Tactical Intelligence & Crime Analytics Platform

![NEXUS Cover](https://via.placeholder.com/1200x400/0a0a0a/00e5ff?text=NEXUS+TACTICAL+INTELLIGENCE+HUB)

**A Palantir-grade synthetic crime digital twin and analytics platform designed for the Karnataka State Police Datathon.**

NEXUS transforms fragmented police records into actionable intelligence by fusing relational databases, geospatial (GIS) context, and graph-based cross-jurisdictional analytics (Silo Buster) into a single cinematic command center experience.

---

## 🎯 The Vision
Police today often investigate incidents in isolated systems. Our goal is to break those silos and transform fragmented records into actionable intelligence. Rather than reacting to crime, commanders gain a live operational picture that supports proactive policing.

NEXUS achieves this through:
1. **Synthetic Digital Twin Generation**: Generating hyper-realistic, interconnected data (FIRs, CCTV, patrols, telecoms) modeling real-world crime behavior without exposing PII.
2. **Hybrid Architecture**: Leveraging PostgreSQL for transactional records and Neo4j for deep graph traversal and mastermind identification.
3. **Cinematic UI/UX**: An interactive, zero-latency dashboard that visualizes cross-jurisdictional campaigns dynamically.

---

## 🏗️ Architecture

```mermaid
graph TD
    subgraph Data Layer
        P[(PostgreSQL)] --> |Relational Data| A[FastAPI Backend]
        N[(Neo4j)] --> |Graph Intelligence| A
        S[Simulator] --> |Synthetic Ground Truth| P
        S --> |Relationships| N
    end

    subgraph Analytics Engine
        A --> |Link Analysis| L[Silo Buster Engine]
        A --> |Geospatial| G[GIS Engine]
        A --> |Explainability| E[XAI Module]
    end

    subgraph Command Center (Next.js)
        L --> F[Frontend]
        G --> F
        E --> F
    end
```

## ✨ Flagship Features

### 1. The Silo Buster (Graph Intelligence)
Detects invisible links between seemingly unrelated FIRs using shared entities (phones, vehicles, syndicates, locations). Visualized via Force-Directed Graphs.
- **Explainable AI (XAI)**: Every AI-drawn connection includes explicit evidence (e.g., `Shared Phone | Distance 3.5km`), avoiding black-box decision making.

### 2. Tactical Intelligence Map (GIS)
Every incident is geospatially contextualized. Features animated patrol deployment, district boundary heatmaps, and a global time-machine replay for tracking active campaigns across Karnataka.

### 3. Executive Dashboard & Live Sim
A real-time metrics hub that features a dynamic Threat Panel and an integrated "Simulate Incident" capability, demonstrating exactly how the system ingests and routes live critical alerts to the map and officer deployments.

---

## 🚀 Quickstart (Running Locally)

NEXUS is designed to run entirely offline for maximum reliability during presentations.

### Prerequisites
- Docker & Docker Compose
- Node.js (v18+)
- Python (3.10+)

### 1. Start Databases (PostgreSQL & Neo4j)
```bash
docker-compose up -d
```

### 2. Run the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Run the Frontend (Command Center)
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000`.

### 4. Optional: Run the Simulator
To generate a completely new synthetic dataset of Karnataka:
```bash
cd simulator
python main.py
```

---

## 🎤 Demo Script Execution
For presentations, NEXUS includes an autopilot `Demo Mode`.
1. Open `http://localhost:3000`.
2. Click **START DEMO** in the top navigation bar.
3. The system will automatically sequence through the Boot Screen, Executive Dashboard, Intelligence Map, Campaign Replay, Silo Buster analysis, and Live Incident Simulation over 30 seconds without any mouse interaction.

### The Core Narrative (The Pitch)
When presenting, avoid just listing features. Tell this story:
> *Police Station A files an FIR. Police Station B files another FIR. Police Station C files a third.*
> 
> *Nobody realizes they are connected.*
> 
> *Our platform ingests this fragmented data and discovers a hidden web: a shared phone, leading to a shared vehicle, caught on a shared CCTV camera, mapping to a single organized campaign, and ultimately revealing the mastermind.* 
>
> *That is the moment we stop reacting to crime, and start anticipating it.*

---

## 💡 FAQ / Pitch Responses

**Why synthetic data?**
Because operational police data is sensitive. Synthetic data allows us to preserve statistical realism and test advanced analytics while protecting citizen privacy.

**How would this integrate with CCTNS?**
In production, the simulator is replaced with a CCTNS ETL pipeline. The analytics engine and presentation layers remain entirely unchanged.

**Why Neo4j?**
Criminal investigations naturally involve interconnected entities—people, phones, vehicles, locations, and financial transactions. Relational joins struggle here, but graph databases traverse these links instantly.

**Is the AI explainable?**
Yes. Every relationship drawn by the system is accompanied by explicit, readable evidence avoiding opaque black-box decisions.

---

*Built for the Karnataka State Police Datathon.*
