"""
FastAPI main application entry point for Instagram Content Automation.

This module wires together all components of the application including:
- API routes and endpoints
- Middleware for error handling, CORS, and session management
- Database connections
- Queue system integration
- Comprehensive error handling

Validates Requirements: All requirements (system integration)
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.api import api_router
from app.middleware.session_middleware import SessionValidationMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware, add_request_id_middleware
from app.core.database import engine
from app.core.redis import get_redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for proper resource management.
    """
    # Startup
    logger.info("Starting Instagram Content Automation API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Test database connection
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    # Test Redis connection
    try:
        redis_client = get_redis()
        redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Instagram Content Automation API")
    
    # Close database connections
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


app = FastAPI(
    title="Instagram Content Automation API",
    description="AI-powered Instagram content generation with face identity consistency",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Add request ID middleware (first, so it's available for all other middleware)
app.middleware("http")(add_request_id_middleware)

# Add comprehensive error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session validation middleware
app.add_middleware(SessionValidationMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Instagram Content Automation API",
        "status": "healthy",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Checks the status of all critical system components:
    - API server
    - Database connection
    - Redis connection
    - Queue system
    
    Returns:
        Health status of all components
    """
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "components": {}
    }
    
    # Check database
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client = get_redis()
        redis_client.ping()
        health_status["components"]["redis"] = "healthy"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check queue system
    try:
        from app.core.queue import get_queue_stats
        queue_stats = get_queue_stats()
        health_status["components"]["queue"] = {
            "status": "healthy",
            "stats": queue_stats
        }
    except Exception as e:
        health_status["components"]["queue"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/api/status")
async def api_status():
    """
    API status endpoint for monitoring.
    
    Provides quick status check without detailed component checks.
    """
    return {
        "status": "operational",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler as a fallback.
    
    This catches any exceptions that weren't caught by the middleware.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred. Please try again.",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )