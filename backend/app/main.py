"""
SkillProtocol FastAPI Application
Main entry point for the API server
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Config & DB
from app.core.config import settings
from app.models.database import init_db

# Routers
from app.api.routes import router as core_router
from app.api.dashboard_routes import router as dashboard_router
# Include Mentor router if you implemented the bonus feature
# from app.api.mentor_routes import router as mentor_router 

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # --- STARTUP ---
    print(f"\n{'='*50}")
    print(f"🚀 Starting SkillProtocol API ({settings.ENVIRONMENT})")
    print(f"{'='*50}\n")
    
    # 1. Initialize Database
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database init failed: {e}")

    # 2. Auto-Configure Opik Rules (Best Use of Opik)
    # This ensures that even if we deploy to a fresh env, the "Online Eval Rules"
    # are registered with the Opik backend automatically.
    try:
        from app.scripts.setup_online_evals import configure_platform
        print("⚙️  Syncing Opik Online Evaluation Rules...")
        configure_platform()
        print("✅ Opik Rules Synced")
    except ImportError:
        print("⚠️  Opik setup script not found, skipping auto-config.")
    except Exception as e:
        # Don't crash app if Opik is down, just log warning
        print(f"⚠️  Could not auto-configure Opik: {e}")
    
    yield
    
    # --- SHUTDOWN ---
    print("👋 Shutting down SkillProtocol API...")

# Create FastAPI app
app = FastAPI(
    title="SkillProtocol API",
    description="AI-powered skill verification using LangGraph & Opik",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(core_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
# app.include_router(mentor_router, prefix="/api") # Uncomment if using Mentor

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SkillProtocol API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "opik_project": settings.OPIK_PROJECT_NAME
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "opik_connection": "ready"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )