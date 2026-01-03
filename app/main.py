"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.controllers import launch_controller, stats_controller


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Track and analyze SpaceX launches using their public API",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(launch_controller.router)
    app.include_router(stats_controller.router)

    return app


# Create app instance
app = create_app()


@app.get("/", tags=["health"])
async def root() -> dict:
    """Root endpoint - API health check."""
    return {
        "message": "SpaceX Launch Tracker API",
        "version": settings.app_version,
        "status": "operational"
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
