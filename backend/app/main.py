"""
BuizSwarm - Autonomous Company Building Platform

FastAPI entry point for the BuizSwarm platform.
Provides a REST API for managing AI-powered autonomous companies.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api.routes import router
from .core.swarm_orchestrator import get_orchestrator
from .core.mcp_client import get_mcp_client, MCP_SERVER_PRESETS

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up BuizSwarm platform...")
    
    # Initialize orchestrator
    orchestrator = get_orchestrator()
    await orchestrator.initialize()
    
    # Register MCP servers
    mcp = get_mcp_client()
    for server_id, server_config in MCP_SERVER_PRESETS.items():
        try:
            await mcp.register_server(
                server_id=server_id,
                name=server_config["name"],
                url=server_config["url"],
                auto_connect=False  # Don't auto-connect in development
            )
            logger.info(f"Registered MCP server: {server_config['name']}")
        except Exception as e:
            logger.warning(f"Failed to register MCP server {server_id}: {e}")
    
    logger.info("BuizSwarm platform started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BuizSwarm platform...")
    
    await orchestrator.shutdown()
    await mcp.close()
    
    logger.info("BuizSwarm platform shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Company Building Platform powered by AI Agents",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [
        "https://buizswarm.com",
        "https://app.buizswarm.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle global exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Include API routes
app.include_router(router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Autonomous Company Building Platform",
        "documentation": "/docs",
        "health": "/health"
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{company_id}")
async def websocket_endpoint(websocket, company_id: str):
    """WebSocket endpoint for real-time company updates."""
    await websocket.accept()
    
    try:
        while True:
            # Get company status
            from .services.company_service import get_company_service
            service = get_company_service()
            status = await service.get_company_status(company_id)
            
            if status:
                await websocket.send_json(status)
            
            # Wait before next update
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=1 if settings.DEBUG else settings.API_WORKERS,
        reload=settings.DEBUG
    )
