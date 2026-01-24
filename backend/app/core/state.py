"""
LangGraph State Schema - Production Version 2.0
Defines the shared state that flows through the SkillProtocol agentic workflow.
"""

from typing import TypedDict, Literal, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator
from datetime import datetime


class AnalysisState(TypedDict):
    """
    The central state object that all agents read from and write to.
    Acts as the 'shared memory' for the SkillProtocol Board of Agents.
    """
    
    # ========================================================================
    # INPUT (Set by API endpoint)
    # ========================================================================
    repo_url: str
    """GitHub repository URL to analyze"""
    
    job_id: str
    """Unique identifier for this analysis job"""
    
    user_id: str
    """User ID requesting the analysis"""
    
    user_github_token: Optional[str]
    """Optional: User's GitHub token for private repo access"""
    
    # ========================================================================
    # PROGRESS TRACKING
    # ========================================================================
    current_step: Literal[
        "validator", "scanner", "reviewer", "grader", "judge", "auditor", "reporter", "complete"
    ]
    """Which agent is currently executing"""
    
    progress: int
    """Overall progress percentage (0-100)"""
    
    # ========================================================================
    # AGENT OUTPUTS
    # ========================================================================
    
    validation: Optional[Dict[str, Any]]
    """
    Output from Validator Agent: Repo metadata and accessibility status.
    """
    
    scan_metrics: Dict[str, Any]
    """
    Output from Scanner Agent (NCrF Layer).
    Must include:
    - ncrf: { total_sloc, estimated_learning_hours, ncrf_base_credits }
    - sample_files: List[Dict] (Raw content of top 3-5 critical files)
    - markers: { has_tests, has_ci_cd, uses_async, etc. }
    """
    
    validation_result: Dict[str, Any]
    """
    Output from Bayesian Validator (Statistical Prior).
    Contains: { bayesian_best_estimate, confidence, expected_range }
    """

    semantic_report: Optional[Dict[str, Any]]
    """
    Output from Reviewer Agent (Architectural Forensics).
    Contains: { key_insight, sophistication_score, key_strengths, key_weaknesses }
    """

    semantic_multiplier: float
    """Qualitative adjustment from Reviewer Agent (0.5 - 1.5)"""
    
    sfia_result: Dict[str, Any]
    """
    Output from Grader Agent & Judge Agent.
    Contains: { sfia_level, level_name, confidence, reasoning }
    - Judge Agent will update these fields with its final verdict.
    - Judge adds: { judge_summary, judge_justification, is_congruent }
    """
    
    audit_result: Optional[Dict[str, Any]]
    """
    Output from Auditor Agent: Result of the CI/CD build check.
    """
    
    # ========================================================================
    # FINAL VERDICTS
    # ========================================================================
    final_credits: Optional[float]
    """Final calculated credits: NCrF_Base * SFIA_Mult * Semantic_Mult * Reality_Mult"""

    # ========================================================================
    # OBSERVABILITY & METADATA
    # ========================================================================
    opik_trace_id: Optional[str]
    """Opik trace ID for immutable reasoning proof"""
    
    errors: Annotated[List[str], operator.add]
    """Accumulated errors from all agents."""
    
    started_at: Optional[str]
    """ISO timestamp when analysis started"""
    
    completed_at: Optional[str]
    """ISO timestamp when analysis completed"""
    
    should_skip: bool
    """Flag to stop the workflow if validation fails"""
    
    skip_reason: Optional[str]
    """Explanation for workflow termination"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_initial_state(
    repo_url: str, 
    user_id: str, 
    job_id: str, 
    user_github_token: Optional[str] = None
) -> AnalysisState:
    """
    Creates the initial state for a new analysis job.
    Initializes all dictionary-based outputs to empty objects to prevent None errors.
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
    Maps agent step to progress percentage for frontend visualization.
    """
    progress_map = {
        "validator": 10,
        "scanner": 30,
        "reviewer": 50,  # Dedicated progress slot for Semantic Review
        "grader": 70,
        "judge": 85,     # The heavy lifting of arbitration
        "auditor": 90,
        "reporter": 95,
        "complete": 100
    }
    return progress_map.get(step, 0)