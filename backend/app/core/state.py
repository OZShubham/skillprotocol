"""
LangGraph State Schema - WITH MENTOR SUPPORT
"""

from typing import TypedDict, Literal, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator
from datetime import datetime


class AnalysisState(TypedDict):
    """
    The central state object that all agents read from and write to.
    Now includes mentorship_plan for growth recommendations.
    """
    
    # ========================================================================
    # INPUT
    # ========================================================================
    repo_url: str
    job_id: str
    user_id: str
    user_github_token: Optional[str]
    
    # ========================================================================
    # PROGRESS TRACKING
    # ========================================================================
    current_step: Literal[
        "validator", "scanner", "reviewer", "grader", "judge", "auditor", "mentor", "reporter", "complete"
    ]
    progress: int
    
    # ========================================================================
    # AGENT OUTPUTS
    # ========================================================================
    validation: Optional[Dict[str, Any]]
    scan_metrics: Dict[str, Any]
    validation_result: Dict[str, Any]
    semantic_report: Optional[Dict[str, Any]]
    semantic_multiplier: float
    sfia_result: Dict[str, Any]
    audit_result: Optional[Dict[str, Any]]
    
    # NEW: Mentorship output
    mentorship_plan: Optional[Dict[str, Any]]
    """
    Output from Mentor Agent: Personalized growth plan.
    Contains:
    - current_assessment: strengths, weaknesses, justification
    - next_level_requirements: missing skills, patterns, practices
    - actionable_roadmap: step-by-step action items
    - quick_wins: easy improvements
    - credit_projection: potential credit increase
    """
    
    # ========================================================================
    # FINAL VERDICTS
    # ========================================================================
    final_credits: Optional[float]
    
    # ========================================================================
    # OBSERVABILITY
    # ========================================================================
    opik_trace_id: Optional[str]
    errors: Annotated[List[str], operator.add]
    started_at: Optional[str]
    completed_at: Optional[str]
    should_skip: bool
    skip_reason: Optional[str]


def create_initial_state(
    repo_url: str, 
    user_id: str, 
    job_id: str, 
    user_github_token: Optional[str] = None
) -> AnalysisState:
    """
    Creates the initial state for a new analysis job.
    """
    return AnalysisState(
        repo_url=repo_url,
        user_id=user_id,
        job_id=job_id,
        user_github_token=user_github_token,
        current_step="validator",
        progress=0,
        validation=None,
        scan_metrics={},
        validation_result={},
        semantic_report=None,
        semantic_multiplier=1.0,
        sfia_result={},
        audit_result=None,
        mentorship_plan=None,  # NEW FIELD
        final_credits=None,
        opik_trace_id=None,
        errors=[],
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        should_skip=False,
        skip_reason=None
    )


def get_progress_for_step(step: str) -> int:
    """
    Maps agent step to progress percentage.
    UPDATED: Now includes 'mentor' step.
    """
    progress_map = {
        "validator": 10,
        "scanner": 25,
        "reviewer": 40,
        "grader": 60,
        "judge": 75,
        "auditor": 85,
        "mentor": 92,    # NEW STEP
        "reporter": 95,
        "complete": 100
    }
    return progress_map.get(step, 0)