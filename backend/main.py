"""
Moo Director - Multi-Agent System for 3D Workflows
Main FastAPI application entry point.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api import router
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _configure_langsmith(settings) -> bool:
    """
    Configure LangSmith tracing if API key is provided.
    
    Returns:
        True if LangSmith is enabled, False otherwise.
    """
    if settings.langchain_api_key and settings.langchain_api_key != "your_langsmith_api_key_here":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
        return True
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    settings = get_settings()
    logger.info("Starting Moo Director API")
    logger.info(f"Debug mode: {settings.debug}")
    
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY not set - LLM features will not work")
    
    # Configure LangSmith tracing
    if _configure_langsmith(settings):
        logger.info(f"LangSmith tracing enabled for project: {settings.langchain_project}")
    else:
        logger.info("LangSmith tracing disabled (no API key configured)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Moo Director API")


# Create FastAPI app
app = FastAPI(
    title="Moo Director",
    description="""
    Multi-agent AI system for 3D workflow automation.
    
    ## Agents
    
    - **Orchestrator**: Lead Art Director - decomposes requests and coordinates agents
    - **Librarian**: Asset Fetcher - retrieves 3D assets from the library
    - **Architect**: Layout Artist - places objects in 3D space
    - **Material Scientist**: Look-Dev Artist - applies PBR materials
    - **Cinematographer**: Lighting Director - sets up lights and camera
    - **Critic**: Quality Controller - validates and ensures quality
    
    ## Workflow
    
    1. Submit a natural language prompt describing your 3D scene
    2. The Orchestrator breaks down the request
    3. Agents collaborate to build the scene
    4. The Critic validates and requests revisions if needed
    5. Final scene data is returned with validation report
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["scene"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Moo Director",
        "version": "1.0.0",
        "description": "Multi-agent AI system for 3D workflow automation",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
