"""
FTex Decision Intelligence Platform - Main Application Entry Point

A comprehensive financial crime detection and decision intelligence platform
featuring entity resolution, graph analytics, and real-time monitoring.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.core.config import settings
from app.api import router as api_router
from app.core.database import init_db
from app.services.opensearch_service import OpenSearchService
from app.services.neo4j_service import Neo4jService


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("🚀 Starting FTex Decision Intelligence Platform...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Initialize OpenSearch
    try:
        opensearch_service = OpenSearchService()
        await opensearch_service.initialize_indices()
        logger.info("✅ OpenSearch indices initialized")
    except Exception as e:
        logger.warning(f"⚠️ OpenSearch initialization warning: {e}")
    
    # Initialize Neo4j
    try:
        neo4j_service = Neo4jService()
        await neo4j_service.verify_connection()
        logger.info("✅ Neo4j connection verified")
    except Exception as e:
        logger.warning(f"⚠️ Neo4j connection warning: {e}")
    
    logger.info("✅ FTex Platform started successfully!")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down FTex Platform...")
    logger.info("👋 Goodbye!")


# Create FastAPI application
app = FastAPI(
    title="FTex Decision Intelligence Platform",
    description="""
## 🎯 FTex - Financial Crime Detection & Decision Intelligence

A comprehensive platform for detecting financial crimes and enabling smarter 
decision-making through connected, trusted data.

### Features:
- **Entity Resolution**: Identify and link related entities across data sources
- **Graph Analytics**: Visualize complex relationships and networks
- **Transaction Monitoring**: Real-time fraud and AML detection
- **Risk Scoring**: Advanced ML-based risk assessment
- **KYC/CDD Management**: Customer due diligence workflows
- **Regulatory Compliance**: FATF, MAS, and global standards support

### Technical Capabilities:
- Apache Spark for large-scale data processing
- OpenSearch for full-text search and analytics
- Neo4j for graph-based entity relationships
- Real-time streaming with Kafka
- RESTful API with OpenAPI 3.0

Built for Tier 1 Banking organisations in the APAC region.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with platform information."""
    return {
        "name": "FTex Decision Intelligence Platform",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "up",
            "cache": "up",
            "search": "up",
            "graph": "up"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

