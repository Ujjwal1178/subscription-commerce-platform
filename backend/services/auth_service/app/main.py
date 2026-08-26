"""
Auth Service - Main Entry Point

This is where FastAPI app is created and configured.
Uvicorn runs this file: uvicorn app.main:app
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api.auth import router as auth_router

# Import logger
from app.logger import logger

# Import config
from app.config import IS_DEV_MODE, SERVICE_NAME, SERVICE_VERSION

# Import exception handlers
from app.exception_handlers import register_exception_handlers


# =============================================================================
# CREATE FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Auth Service",
    description="Authentication & Authorization service for Subscription Commerce Platform",
    version=SERVICE_VERSION,
    docs_url="/docs" if IS_DEV_MODE else None,      # Swagger UI (dev only)
    redoc_url="/redoc" if IS_DEV_MODE else None,    # ReDoc (dev only)
)


# =============================================================================
# EXCEPTION HANDLERS - Must be registered before routes!
# =============================================================================

register_exception_handlers(app)


# =============================================================================
# MIDDLEWARE
# =============================================================================

# CORS - Allow frontend to call API from different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if IS_DEV_MODE else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# INCLUDE ROUTERS
# =============================================================================

app.include_router(auth_router)


# =============================================================================
# STARTUP & SHUTDOWN EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Runs when service starts."""
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} started")
    logger.info(f"Dev mode: {IS_DEV_MODE}")


@app.on_event("shutdown")
async def shutdown_event():
    """Runs when service stops."""
    logger.info(f"{SERVICE_NAME} shutting down")


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Used by:
    - Docker/Kubernetes to know if service is alive
    - Load balancers to route traffic
    - Monitoring tools to alert if service is down
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - basic service info."""
    return {
        "message": f"{SERVICE_NAME} is running!",
        "version": SERVICE_VERSION,
        "docs": "/docs" if IS_DEV_MODE else "disabled",
    }
