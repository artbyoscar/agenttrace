from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from src.api.routes import traces, projects, analytics
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting AgentTrace API...")
    yield
    # Shutdown
    print("Shutting down AgentTrace API...")


app = FastAPI(
    title="AgentTrace API",
    description="API for AI agent tracing and observability",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(traces.router, prefix="/api/v1/traces", tags=["traces"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/")
async def root():
    return {"message": "AgentTrace API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
