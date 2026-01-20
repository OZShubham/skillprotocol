"""
LangGraph State Schema
Defines the shared state that flows through all agents
"""

from typing import TypedDict, Literal, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator


class AnalysisState(TypedDict):
    """
    The central state object that all agents read from and write to.
    
    Think of this as the "memory" that agents share.
    Each agent updates specific fields and passes it to the next agent.
    """
    
    # ========================================================================
    # INPUT (Set by API endpoint)
    # ========================================================================
    repo_url: str
    """GitHub repository URL to analyze"""
    
    user_id: str
    """User ID requesting the analysis"""
    
    job_id: str
    """Unique identifier for this analysis job"""
    
    user_github_token: Optional[str]
    """Optional: User's GitHub token for private repo access"""
    
    # ========================================================================
    # PROGRESS TRACKING (Updated by each agent)
    # ========================================================================
    current_step: Literal["validator", "scanner", "grader", "auditor", "reporter", "complete"]
    """Which agent is currently executing"""
    
    progress: int
    """Overall progress percentage (0-100)"""
    
    # ========================================================================
    # AGENT OUTPUTS (Each agent writes to its own field)
    # ========================================================================
    
    validation: Optional[Dict[str, Any]]
    """
    Output from Validator Agent
    Example:
    {
        "is_valid": true,
        "owner": "user",
        "repo_name": "awesome-project",
        "size_kb": 45000,
        "language": "Python",
        "has_readme": true
    }
    """
    
    scan_metrics: Optional[Dict[str, Any]]
    """
    Output from Scanner Agent
    Example:
    {
        "ncrf": {
            "total_sloc": 5000,
            "estimated_learning_hours": 50.5,
            "ncrf_base_credits": 1.68
        },
        "markers": {
            "has_tests": true,
            "has_docker": false,
            "uses_async": true
        }
    }
    """
    
    sfia_result: Optional[Dict[str, Any]]
    """
    Output from Grader Agent
    Example:
    {
        "sfia_level": 4,
        "level_name": "Enable",
        "confidence": 0.92,
        "reasoning": "Code shows OOP patterns and testing",
        "evidence": ["Unit tests found", "Class-based design"],
        "retry_count": 0
    }
    """
    
    audit_result: Optional[Dict[str, Any]]
    """
    Output from Auditor Agent
    Example:
    {
        "reality_check_passed": true,
        "github_actions_status": "success",
        "penalty_applied": false
    }
    """
    
    final_credits: Optional[float]
    """Final calculated credits (set by Reporter Agent)"""
    
    # ========================================================================
    # OBSERVABILITY
    # ========================================================================
    opik_trace_id: Optional[str]
    """Opik trace ID for full transparency"""
    
    errors: Annotated[List[str], operator.add]
    """
    Accumulated errors from all agents.
    Using operator.add means each agent can append to this list.
    """
    
    # ========================================================================
    # METADATA
    # ========================================================================
    started_at: Optional[str]
    """ISO timestamp when analysis started"""
    
    completed_at: Optional[str]
    """ISO timestamp when analysis completed"""
    
    # ========================================================================
    # CONTROL FLOW (Used by routing logic)
    # ========================================================================
    should_skip: bool
    """Flag to skip remaining agents if validation fails"""
    
    skip_reason: Optional[str]
    """Reason for skipping (e.g., "Repo too large")"""


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
    Creates the initial state for a new analysis job
    """
    from datetime import datetime
    
    return AnalysisState(
        # Input
        repo_url=repo_url,
        user_id=user_id,
        job_id=job_id,
        user_github_token=user_github_token,
        
        # Progress
        current_step="validator",
        progress=0,
        
        # Agent outputs (all None initially) - **IMPORTANT: Use None, not {}**
        validation=None,
        scan_metrics=None,
        sfia_result=None,  # ← Make sure this is None, not {}
        audit_result=None,
        final_credits=None,
        
        # Observability
        opik_trace_id=None,
        errors=[],  # ← Empty list, not None
        
        # Metadata
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        
        # Control flow
        should_skip=False,
        skip_reason=None
    )

def get_progress_for_step(step: str) -> int:
    """
    Maps agent step to progress percentage
    """
    progress_map = {
        "validator": 10,
        "scanner": 40,
        "grader": 70,
        "auditor": 85,
        "reporter": 95,
        "complete": 100
    }
    return progress_map.get(step, 0)