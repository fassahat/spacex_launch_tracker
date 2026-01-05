"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.controllers import launch_controller, stats_controller, web_controller, webhook_controller
from app.services.background_service import start_background_service


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

    # Start background service for webhook notifications
    start_background_service()

    # Register routers
    app.include_router(launch_controller.router)
    app.include_router(stats_controller.router)
    app.include_router(web_controller.router)
    app.include_router(webhook_controller.router)

    return app


# Create app instance
app = create_app()

# Setup templates
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse, tags=["web"])
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/api", tags=["health"])
async def root() -> dict:
    """API health check."""
    return {
        "message": "SpaceX Launch Tracker API",
        "version": settings.app_version,
        "status": "operational"
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
