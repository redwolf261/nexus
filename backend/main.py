from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routers import core, analytics

app = FastAPI(
    title="NEXUS Intelligence Platform API",
    description="Backend API for querying the frozen dataset and serving the Tactical Intelligence Dashboard. Includes full Neo4j Graph Analytics and PostgreSQL relational data.",
    version="1.1.0",
    contact={
        "name": "NEXUS Engineering",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for hackathon flexibility (Netlify domains can change)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS Intelligence Platform API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
