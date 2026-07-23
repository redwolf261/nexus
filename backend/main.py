import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.routers import core, analytics, investigations, intelligence
from backend.core.logging import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.core.limiter import limiter

app = FastAPI(
    title="NEXUS Intelligence Platform API",
    description="Backend API for querying the frozen dataset and serving the Tactical Intelligence Dashboard. Includes full Neo4j Graph Analytics and PostgreSQL relational data.",
    version="1.1.0",
    contact={
        "name": "NEXUS Engineering",
    }
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Hardened CORS policy per Task 10
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Locked down to frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], # Fixed methods
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Security Headers & Logging Middleware (Tasks 8, 10)
@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Attach to request state for inner logging if needed
    request.state.request_id = request_id

    try:
        response = await call_next(request)
        process_time_ms = (time.time() - start_time) * 1000
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        
        logger.info(
            f"{request.method} {request.url.path} {response.status_code}",
            extra={"request_id": request_id, "duration": round(process_time_ms, 2)}
        )
        return response
    except Exception as e:
        process_time_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Unhandled Exception: {str(e)}", 
            exc_info=True,
            extra={"request_id": request_id, "duration": round(process_time_ms, 2)}
        )
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

from backend.api.routers import core, analytics, investigations, intelligence, ws, events, system, tasks, assignment, governance, command_center, investigation_workspace, executive_dashboard
from backend.api.routers import auth
from fastapi import Depends
from backend.auth.deps import get_current_user

app.include_router(auth.router)

# investigations router handles its own deps since it needs different roles for different endpoints
app.include_router(investigations.router)
app.include_router(ws.router)

app.include_router(core.router, dependencies=[Depends(get_current_user)])
app.include_router(analytics.router, dependencies=[Depends(get_current_user)])
app.include_router(intelligence.router, dependencies=[Depends(get_current_user)])
app.include_router(events.router, dependencies=[Depends(get_current_user)])
app.include_router(system.router, dependencies=[Depends(get_current_user)])
app.include_router(tasks.router, dependencies=[Depends(get_current_user)])
app.include_router(assignment.router, dependencies=[Depends(get_current_user)])
app.include_router(governance.router, dependencies=[Depends(get_current_user)])
app.include_router(command_center.router, dependencies=[Depends(get_current_user)])
app.include_router(investigation_workspace.router, dependencies=[Depends(get_current_user)])
app.include_router(executive_dashboard.router, dependencies=[Depends(get_current_user)])






from backend.database import engine
from sqlalchemy import text
from backend.core.logging import logger

@app.on_event("startup")
def startup_event():
    logger.info("Initializing database extensions and indexes...")
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_person_name_trgm ON persons USING gin (name_en gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_person_alias_trgm ON persons USING gin (first_name_en gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_fir_desc_trgm ON firs USING gin (description_en gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_fir_comp_trgm ON firs USING gin (complainant_name gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_vehicle_plate_trgm ON vehicles USING gin (license_plate gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_vehicle_make_trgm ON vehicles USING gin (make gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_vehicle_model_trgm ON vehicles USING gin (model gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_criminal_name_trgm ON criminals USING gin (name_en gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_criminal_alias_trgm ON criminals USING gin (alias_names gin_trgm_ops);',
                'CREATE INDEX IF NOT EXISTS idx_criminal_exp_trgm ON criminals USING gin (expertise gin_trgm_ops);',
            ]
            for idx in indexes:
                conn.execute(text(idx))
                
            # tsvector for FIR description
            conn.execute(text('ALTER TABLE firs ADD COLUMN IF NOT EXISTS search_vector tsvector;'))
            conn.execute(text("UPDATE firs SET search_vector = to_tsvector('english', coalesce(description_en, ''));"))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_fir_search_vector ON firs USING gin(search_vector);'))
            
            # Phase 6.3C Migrations
            migrations = [
                'ALTER TABLE investigations ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;',
                'ALTER TABLE investigations ADD COLUMN IF NOT EXISTS last_sequence INTEGER DEFAULT 0 NOT NULL;',
                'ALTER TABLE investigation_notes ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;',
                'ALTER TABLE events ADD COLUMN IF NOT EXISTS user_id VARCHAR;',
                'ALTER TABLE events ADD COLUMN IF NOT EXISTS sequence INTEGER;',
                'CREATE INDEX IF NOT EXISTS idx_events_sequence ON events(sequence);',
                # ── Phase 8.2: Officer capability columns (additive on existing table) ──
                "ALTER TABLE officers ADD COLUMN IF NOT EXISTS subdivision VARCHAR;",
                "ALTER TABLE officers ADD COLUMN IF NOT EXISTS years_experience INTEGER;",
                "ALTER TABLE officers ADD COLUMN IF NOT EXISTS maximum_capacity INTEGER DEFAULT 10;",
                "ALTER TABLE officers ADD COLUMN IF NOT EXISTS availability_status VARCHAR DEFAULT 'ON_DUTY';",
                "ALTER TABLE officers ADD COLUMN IF NOT EXISTS current_case_count INTEGER DEFAULT 0;",
                "ALTER TABLE officers ADD COLUMN IF NOT EXISTS current_task_count INTEGER DEFAULT 0;",
                "ALTER TABLE officers ADD COLUMN IF NOT EXISTS leave_ends_on DATE;",
                "ALTER TABLE officers ADD COLUMN IF NOT EXISTS capability_version INTEGER DEFAULT 1;",
                "CREATE INDEX IF NOT EXISTS idx_officers_availability ON officers(availability_status);",
                "CREATE INDEX IF NOT EXISTS idx_officers_subdivision ON officers(subdivision);",
                # Backfill sensible defaults for existing rows
                "UPDATE officers SET availability_status = 'ON_DUTY' WHERE availability_status IS NULL;",
                "UPDATE officers SET maximum_capacity = 10 WHERE maximum_capacity IS NULL;",
                "UPDATE officers SET current_case_count = 0 WHERE current_case_count IS NULL;",
                "UPDATE officers SET current_task_count = 0 WHERE current_task_count IS NULL;",
                "UPDATE officers SET years_experience = tenure_years WHERE years_experience IS NULL AND tenure_years IS NOT NULL;",
            ]
            for mig in migrations:
                try:
                    conn.execute(text(mig))
                except Exception as e:
                    logger.warning(f"Migration step failed (might be SQLite): {e}")

            from backend.db.schema import Base
            Base.metadata.create_all(bind=engine)
            
            logger.info("Database extensions and indexes initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database indexes: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS Intelligence Platform API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
