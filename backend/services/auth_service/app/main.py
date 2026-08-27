"""Auth Service - Main Entry Point. Run with: uvicorn app.main:app"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.logger import logger
from app.config import IS_DEV_MODE, SERVICE_NAME, SERVICE_VERSION
from app.exception_handlers import register_exception_handlers


app = FastAPI(
    title="Auth Service",
    description="Authentication & Authorization service for Subscription Commerce Platform",
    version=SERVICE_VERSION,
    docs_url="/docs" if IS_DEV_MODE else None,
    redoc_url="/redoc" if IS_DEV_MODE else None,
)

# Register exception handlers
register_exception_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if IS_DEV_MODE else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} started | Dev mode: {IS_DEV_MODE}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"{SERVICE_NAME} shutting down")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check for Docker/K8s/Load balancers."""
    return {"status": "healthy", "service": SERVICE_NAME, "version": SERVICE_VERSION}


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - basic service info."""
    return {"message": f"{SERVICE_NAME} is running!", "version": SERVICE_VERSION}
