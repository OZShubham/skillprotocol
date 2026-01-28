"""
SkillProtocol LangGraph Orchestrator - WITH MENTOR AGENT
Handles multi-agent handoff including the new Mentor agent for growth recommendations.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import Opik tracking
from opik.integrations.langchain import OpikTracer, track_langgraph

# App Imports
from app.core.config import settings
from app.core.state import AnalysisState, create_initial_state
from app.agents.validator import validate_repository
from app.agents.scanner import scan_codebase
from app.agents.reviewer import review_semantics
from app.agents.grader import grade_sfia_level
from app.agents.judge import arbitrate_level
from app.agents.auditor import reality_check
from app.agents.mentor import provide_mentorship  # NEW IMPORT
from app.agents.reporter import store_and_report

# ============================================================================
# ROUTING LOGIC (UPDATED)
# ============================================================================

def should_proceed_to_scanner(state: AnalysisState) -> Literal["scanner", "reporter"]:
    """Decision after validation"""
    if state.get("should_skip", False):
        print(f"⏭️  [Router] Skipping analysis: {state.get('skip_reason')}")
        return "reporter"
    
    validation = state.get("validation")
    if not validation or not validation.get("is_valid", False):
        print(f"⏭️  [Router] Validation failed")
        return "reporter"
    
    print("✅ [Router] Validation passed, proceeding to scanner")
    return "scanner"


def should_proceed_to_reviewer(state: AnalysisState) -> Literal["reviewer", "reporter"]:
    """Decision after scanning"""
    scan_metrics = state.get("scan_metrics")
    if not scan_metrics:
        print("⏭️  [Router] No scan metrics, skipping to reporter")
        return "reporter"
    
    ncrf = scan_metrics.get("ncrf", {})
    total_sloc = ncrf.get("total_sloc", 0)
    
    if total_sloc < 10:
        print(f"⏭️  [Router] Not enough code ({total_sloc} SLOC), skipping to reporter")
        return "reporter"
    
    print(f"✅ [Router] Found {total_sloc} SLOC, proceeding to reviewer")
    return "reviewer"


def should_retry_grader(state: AnalysisState) -> Literal["grader", "judge"]:
    """Decision after grading"""
    sfia_result = state.get("sfia_result")
    if not sfia_result:
        return "judge"
    
    confidence = sfia_result.get("confidence", 1.0)
    retry_count = sfia_result.get("retry_count", 0)
    
    if confidence < 0.7 and retry_count == 0:
        print(f"🔄 [Router] Low confidence ({confidence:.2f}), retrying grader")
        state["sfia_result"]["retry_count"] = 1
        return "grader"
    
    print(f"✅ [Router] Grader finished, proceeding to Judge")
    return "judge"


def should_provide_mentorship(state: AnalysisState) -> Literal["mentor", "reporter"]:
    """
    Decide if we should provide mentorship based on Analysis State.
    Architectural Logic:
    1. Did we find code? (Scanner)
    2. Did we pass the reality check? (Auditor)
    3. Is there room to grow? (SFIA Level < 5)
    """
    
    # 1. Check if we actually have code analysis (Scanner Output)
    ncrf = state.get("scan_metrics", {}).get("ncrf", {})
    base_credits = ncrf.get("ncrf_base_credits", 0)
    
    if base_credits <= 0:
        print("⏭️  [Router] No measurable code found, skipping mentorship")
        return "reporter"
    
    # 2. Check Reality Check (Auditor Output)
    # If the code doesn't build, we shouldn't mentor them on 'growth' yet; 
    # they need to fix their build first.
    audit_result = state.get("audit_result", {})
    if not audit_result.get("reality_check_passed", False):
        print("⏭️  [Router] Reality check failed (Broken Build), skipping mentorship")
        return "reporter"

    # 3. Check SFIA Ceiling (Grader/Judge Output)
    # Level 5 experts don't need this automated mentorship.
    sfia_result = state.get("sfia_result", {})
    current_level = sfia_result.get("sfia_level", 0)
    
    if current_level >= 5:
        print(f"⏭️  [Router] Expert Level {current_level} detected, skipping standard mentorship")
        return "reporter"
    
    # Success: All pre-requisites met.
    print(f"✅ [Router] Valid Analysis (L{current_level}) -> Routing to Mentor Agent")
    return "mentor"


# ============================================================================
# GRAPH DEFINITION (UPDATED)
# ============================================================================

def create_analysis_graph():
    """Creates the LangGraph workflow WITH Mentor Agent"""
    
    workflow = StateGraph(AnalysisState)
    
    # Add all nodes including MENTOR
    workflow.add_node("validator", validate_repository)
    workflow.add_node("scanner", scan_codebase)
    workflow.add_node("reviewer", review_semantics)
    workflow.add_node("grader", grade_sfia_level)
    workflow.add_node("judge", arbitrate_level)
    workflow.add_node("auditor", reality_check)
    workflow.add_node("mentor", provide_mentorship)  # NEW NODE
    workflow.add_node("reporter", store_and_report)
    
    # Entry point
    workflow.set_entry_point("validator")
    
    # Validator -> Scanner
    workflow.add_conditional_edges(
        "validator",
        should_proceed_to_scanner,
        {"scanner": "scanner", "reporter": "reporter"}
    )
    
    # Scanner -> Reviewer
    workflow.add_conditional_edges(
        "scanner",
        should_proceed_to_reviewer,
        {"reviewer": "reviewer", "reporter": "reporter"}
    )
    
    # Reviewer -> Grader
    workflow.add_edge("reviewer", "grader")
    
    # Grader -> (Retry) OR (Judge)
    workflow.add_conditional_edges(
        "grader",
        should_retry_grader,
        {"grader": "grader", "judge": "judge"}
    )
    
    # Judge -> Auditor
    workflow.add_edge("judge", "auditor")
    
    # Auditor -> Mentor (NEW EDGE)
    workflow.add_conditional_edges(
        "auditor",
        should_provide_mentorship,
        {"mentor": "mentor", "reporter": "reporter"}
    )
    
    # Mentor -> Reporter (NEW EDGE)
    workflow.add_edge("mentor", "reporter")
    
    # Reporter -> END
    workflow.add_edge("reporter", END)
    
    # Compile with Memory
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# Global graph instance
analysis_graph = create_analysis_graph()


# ============================================================================
# EXECUTION INTERFACE
# ============================================================================

async def run_analysis(
    repo_url: str,
    user_id: str,
    job_id: str,
    user_github_token: str = None
) -> AnalysisState:
    """
    High-level function to run the full analysis workflow.
    Now includes Mentor agent for growth recommendations.
    """
    
    print(f"\n{'='*70}")
    print(f"🚀 Starting SkillProtocol Analysis (WITH MENTOR)")
    print(f"   Job ID: {job_id}")
    print(f"   Repo: {repo_url}")
    print(f"   User: {user_id}")
    print(f"{'='*70}\n")
    
    # Create Initial State
    initial_state = create_initial_state(
        repo_url=repo_url,
        user_id=user_id,
        job_id=job_id,
        user_github_token=user_github_token
    )

    # Configure Opik Tracer
    opik_tracer = OpikTracer(
        project_name=settings.OPIK_PROJECT_NAME,
        tags=["production", "skill-verification", "with-mentor"],
        metadata={
            "user_id": user_id,
            "repo_url": repo_url,
            "job_id": job_id
        }
    )
    
    # Wrap graph with tracking
    tracked_graph = track_langgraph(
        analysis_graph,
        opik_tracer=opik_tracer
    )

    # Configure Threading
    config = {
        "configurable": {"thread_id": job_id},
        "metadata": {"opik_thread_id": job_id}
    }
    
    try:
        # Invoke the tracked graph
        final_state = await tracked_graph.ainvoke(initial_state, config)
    except Exception as e:
        print(f"❌ Workflow execution error: {str(e)}")
        initial_state["errors"].append(f"Workflow error: {str(e)}")
        initial_state["current_step"] = "complete"
        initial_state["progress"] = 100
        initial_state["final_credits"] = 0.0
        return initial_state
    
    print(f"\n{'='*70}")
    print(f"✅ Analysis Complete (WITH MENTORSHIP)")
    print(f"   Final Level: {final_state.get('sfia_result', {}).get('sfia_level', 'N/A')}")
    print(f"   Final Credits: {final_state.get('final_credits', 0)}")
    print(f"   Mentorship: {'Provided' if final_state.get('mentorship_plan') else 'Not applicable'}")
    print(f"   Errors: {len(final_state.get('errors', []))}")
    print(f"{'='*70}\n")
    
    return final_state


async def get_analysis_status(job_id: str) -> dict:
    """Gets a snapshot of the ongoing graph state."""
    
    config = {"configurable": {"thread_id": job_id}}
    
    try:
        state_snapshot = await analysis_graph.aget_state(config)
        
        if not state_snapshot or not state_snapshot.values:
            return {
                "status": "not_found",
                "current_step": None,
                "progress": 0
            }
        
        values = state_snapshot.values
        
        # Determine status
        status = "running"
        if not state_snapshot.next and values.get("current_step") == "complete":
            status = "complete"
        elif not state_snapshot.next:
            status = "complete"

        return {
            "status": status,
            "current_step": values.get("current_step"),
            "progress": values.get("progress", 0),
            "errors": values.get("errors", []),
            "final_credits": values.get("final_credits")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }