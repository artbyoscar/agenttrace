"""
AgentTrace Ingestion API - FastAPI Application

High-performance async API for ingesting AI agent traces with:
- Batch span ingestion
- Background processing
- Multiple storage backends
- Health checks and metrics
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from .config import get_settings
from .services.storage import create_storage_backend
from .services.ingestion import IngestionService
from .routers import traces, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Global ingestion service
ingestion_service: IngestionService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting AgentTrace Ingestion API")

    settings = get_settings()

    # Update log level from settings
    logging.getLogger().setLevel(settings.log_level.upper())
    logger.info(f"Log level set to {settings.log_level}")

    # Create storage backend
    logger.info(f"Initializing {settings.storage_backend} storage backend")
    storage = create_storage_backend(
        backend_type=settings.storage_backend,
        storage_path=settings.storage_path,
        s3_bucket=settings.s3_bucket,
        s3_region=settings.s3_region,
        s3_access_key=settings.s3_access_key,
        s3_secret_key=settings.s3_secret_key,
    )

    # Create ingestion service
    global ingestion_service
    ingestion_service = IngestionService(
        storage=storage,
        batch_size=settings.batch_size,
        flush_interval=settings.batch_timeout,
        max_queue_size=settings.max_queue_size,
    )

    # Set ingestion service in routers
    traces.set_ingestion_service(ingestion_service)

    # Start ingestion worker
    await ingestion_service.start()
    logger.info("Ingestion service started")

    logger.info("AgentTrace Ingestion API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down AgentTrace Ingestion API")

    # Shutdown ingestion service
    if ingestion_service:
        await ingestion_service.shutdown()
        logger.info("Ingestion service stopped")

    logger.info("AgentTrace Ingestion API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AgentTrace Ingestion API",
    description="High-performance API for ingesting AI agent traces",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Get settings
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with detailed error messages.

    Returns structured error response with field-level details.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected errors.

    Logs the error and returns a generic error response.
    """
    logger.error(f"Unexpected error on {request.url.path}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.log_level == "debug" else None,
        },
    )


# Register routers
app.include_router(traces.router)
app.include_router(health.router)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint.

    Returns API information.
    """
    return {
        "name": "AgentTrace Ingestion API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/v1/health",
        "metrics": "/v1/metrics",
    }


# For development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ingestion_api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level,
    )
