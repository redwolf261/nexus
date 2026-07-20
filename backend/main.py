import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.routers import core, analytics
from backend.core.logging import logger

app = FastAPI(
    title="NEXUS Intelligence Platform API",
    description="Backend API for querying the frozen dataset and serving the Tactical Intelligence Dashboard. Includes full Neo4j Graph Analytics and PostgreSQL relational data.",
    version="1.1.0",
    contact={
        "name": "NEXUS Engineering",
    }
)

# Hardened CORS policy per Task 10
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Locked down to frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"], # Restricted methods
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

app.include_router(core.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS Intelligence Platform API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
