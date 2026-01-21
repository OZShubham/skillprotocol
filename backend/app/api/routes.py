"""
API Routes - FIXED VERSION
Now properly surfaces validation errors and handles private repos
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl, validator
from typing import Optional
import uuid

from sqlalchemy import select, desc
from app.models.database import get_db, Repository, CreditLedger
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_analysis, get_analysis_status


router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request body for /analyze endpoint"""
    repo_url: str  # Changed from HttpUrl to allow validation
    user_id: Optional[str] = "anonymous"
    github_token: Optional[str] = None
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        """Basic validation before sending to agent"""
        if not v or not v.strip():
            raise ValueError("Repository URL is required")
        
        # Allow both with/without https
        v = v.strip()
        if not ('github.com' in v):
            raise ValueError("Only GitHub repositories are supported")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "repo_url": "https://github.com/fastapi/fastapi",
                "user_id": "user-123",
                "github_token": "ghp_xxxxx (optional, for private repos)"
            }
        }


class AnalyzeResponse(BaseModel):
    """Response from /analyze endpoint"""
    job_id: str
    status: str
    message: str
    estimated_time_seconds: int = 60


class StatusResponse(BaseModel):
    """Response from /status endpoint"""
    job_id: str
    status: str
    current_step: Optional[str] = None
    progress: int
    errors: list[str] = []
    final_credits: Optional[float] = None
    validation: Optional[dict] = None  # NEW: Include validation for error details


class ResultResponse(BaseModel):
    """Response from /result endpoint"""
    job_id: str
    repo_url: str
    final_credits: float
    sfia_level: Optional[int] = None
    sfia_level_name: Optional[str] = None
    opik_trace_url: Optional[str] = None
    validation: Optional[dict] = None
    scan_metrics: Optional[dict] = None
    audit_result: Optional[dict] = None
    errors: list[str] = []
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    sfia_result: Optional[dict] = None       # To pass confidence & reasoning
    validation_result: Optional[dict] = None # To pass Bayesian stats


# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

analysis_jobs = {}


# ============================================================================
# ENDPOINT 1: START ANALYSIS (FIXED)
# ============================================================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db) 
):
    """
    Start a new repository analysis.
    
    FIXED:
    - Better error handling for validation failures
    - Proper private repo detection
    - Clear error messages returned to frontend
    """
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Store initial job info
    # Store initial job info
    analysis_jobs[job_id] = {
        "job_id": job_id,
        "repo_url": request.repo_url,
        "user_id": request.user_id,
        "status": "queued",
        "has_user_token": bool(request.github_token),
        "validation": None,
        "errors": []
    }
    
    # Run analysis in background
    async def run_in_background():
        try:
            # Run the LangGraph workflow
            final_state = await run_analysis(
                repo_url=request.repo_url,
                user_id=request.user_id,
                job_id=job_id,
                user_github_token=request.github_token
            )
            
            # Check if validation failed
            if final_state.get("should_skip"):
                analysis_jobs[job_id]["status"] = "failed"
                analysis_jobs[job_id]["validation"] = final_state.get("validation")
                analysis_jobs[job_id]["errors"] = final_state.get("errors", [])
                analysis_jobs[job_id]["skip_reason"] = final_state.get("skip_reason")
            else:
                # Success
                analysis_jobs[job_id]["status"] = "complete"
                analysis_jobs[job_id]["result"] = final_state
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            analysis_jobs[job_id]["status"] = "error"
            analysis_jobs[job_id]["error"] = str(e)
            analysis_jobs[job_id]["errors"] = [str(e)]
    
    background_tasks.add_task(run_in_background)
    
    return AnalyzeResponse(
        job_id=job_id,
        status="queued",
        message="Analysis started. Poll /status/{job_id} for progress.",
        estimated_time_seconds=60
    )


# ============================================================================
# ENDPOINT 2: CHECK STATUS (FIXED)
# ============================================================================

@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Get the current status of an analysis job.
    
    FIXED:
    - Returns validation errors properly
    - Distinguishes between "failed" and "error"
    """
    
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    # Handle validation failure
    if job["status"] == "failed":
        return StatusResponse(
            job_id=job_id,
            status="failed",
            progress=10,  # Stopped at validator
            errors=job.get("errors", []),
            validation=job.get("validation")  # Contains error_type
        )
    
    # Handle other errors
    if job["status"] == "error":
        return StatusResponse(
            job_id=job_id,
            status="error",
            progress=0,
            errors=[job.get("error", "Unknown error")]
        )
    
    # Job complete
    if job["status"] == "complete":
        result = job.get("result", {})
        return StatusResponse(
            job_id=job_id,
            status="complete",
            current_step="complete",
            progress=100,
            errors=result.get("errors", []),
            final_credits=result.get("final_credits"),
            validation=result.get("validation")
        )
    
    # Job still running - get live status
    status = await get_analysis_status(job_id)
    
    return StatusResponse(
        job_id=job_id,
        status=status.get("status", "running"),
        current_step=status.get("current_step"),
        progress=status.get("progress", 0),
        errors=status.get("errors", [])
    )


# ============================================================================
# ENDPOINT 3: GET FINAL RESULT (FIXED)
# ============================================================================

@router.get("/result/{job_id}", response_model=ResultResponse)
async def get_result(job_id: str):
    """
    Get the final result of a completed analysis.
    
    FIXED:
    - Only returns results for truly complete jobs
    - Returns 400 for failed validations
    """
    
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    # Check if validation failed
    if job["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation failed",
                "validation": job.get("validation"),
                "errors": job.get("errors", [])
            }
        )
    
    # Check if job errored
    if job["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=f"Analysis error: {job.get('error')}"
        )
    
    # Check if job is complete
    if job["status"] != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not complete. Current status: {job['status']}"
        )
    
    result = job.get("result", {})
    
    # Extract data with None checks
    sfia_result = result.get("sfia_result") or {}
    sfia_level = sfia_result.get("sfia_level") if sfia_result else None
    sfia_level_name = sfia_result.get("level_name") if sfia_result else None
    
    opik_trace_id = result.get("opik_trace_id")
    opik_trace_url = None
    if opik_trace_id:
        from app.core.config import settings
        workspace = getattr(settings, 'OPIK_WORKSPACE', 'default')
        opik_trace_url = f"https://www.comet.com/{workspace}/opik/traces/{opik_trace_id}"
    
    return ResultResponse(
        job_id=job_id,
        repo_url=job["repo_url"],
        final_credits=result.get("final_credits", 0.0),
        sfia_level=sfia_level,
        sfia_level_name=sfia_level_name,
        opik_trace_url=opik_trace_url,
        
        # Pass the full dictionaries now
        validation=result.get("validation"),
        scan_metrics=result.get("scan_metrics"),
        audit_result=result.get("audit_result"),
        sfia_result=sfia_result,                 # <--- NEW
        validation_result=result.get("validation_result"), # <--- NEW
        
        errors=result.get("errors", []),
        started_at=result.get("started_at"),
        completed_at=result.get("completed_at")
    )

@router.get("/user/{user_id}/history")
async def get_user_history(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch analysis history directly from the database.
    """
    # Fetch repositories analyzed by this user, ordered by newest first
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == user_id)
        .order_by(desc(Repository.created_at))
    )
    repos = result.scalars().all()
    
    history = []
    for repo in repos:
        history.append({
            "id": repo.repo_fingerprint, # Use fingerprint as ID for frontend consistency
            "job_id": repo.repo_fingerprint,
            "repo_url": repo.repo_url,
            "final_credits": repo.final_credits,
            "sfia_level": repo.sfia_level,
            "created_at": repo.created_at.isoformat(),
            "validation": repo.validation_result,
            # Add other fields needed for certificate
            "sfia_level_name": repo.sfia_result.get("level_name") if repo.sfia_result else None,
            "opik_trace_url": f"https://www.comet.com/skillprotocol/opik/traces/{repo.opik_trace_id}" if repo.opik_trace_id else None
        })
        
    return history


# ============================================================================
# BONUS: LIST ALL JOBS
# ============================================================================

@router.get("/jobs")
async def list_jobs():
    """List all analysis jobs"""
    return {
        "total_jobs": len(analysis_jobs),
        "jobs": [
            {
                "job_id": job_id,
                "repo_url": job["repo_url"],
                "status": job["status"]
            }
            for job_id, job in analysis_jobs.items()
        ]
    }