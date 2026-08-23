"""
Auth Service - Main Entry Point
"""
from fastapi import FastAPI

# -----------------------------------------------------------------------------
# Create FastAPI Application
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Auth Service",
    description="Authentication & Authorization service for Subscription Commerce Platform",
    version="1.0.0",
)


# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
# Why health check?
# - Docker/Kubernetes uses this to know if service is alive
# - Load balancers use this to route traffic
# - Monitoring tools use this to alert if service is down
# -----------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-service"}


# -----------------------------------------------------------------------------
# Root Endpoint (for testing)
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Auth Service is running!"}
