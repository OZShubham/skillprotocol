"""
SkillProtocol LangGraph Orchestrator - FIXED FOR VISUALIZATION
Handles multi-agent handoff, Gemini 3 Flash execution, and Opik Thread Grouping.
"""

from typing import Literal, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# --- KEY IMPORT FOR VISUALIZATION ---
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
from app.agents.reporter import store_and_report

# ============================================================================
# ROUTING LOGIC
# ============================================================================

def should_proceed_to_scanner(state: AnalysisState) -> Literal["scanner", "reporter"]:
    """
    Decision after validation: Should we clone and scan?
    Checks both should_skip AND validation.is_valid
    """
    if state.get("should_skip", False):
        print(f"⏭️  [Router] Skipping analysis: {state.get('skip_reason')}")
        return "reporter"
    
    validation = state.get("validation")
    if not validation:
        print("⏭️  [Router] No validation data, skipping to reporter")
        return "reporter"
    
    if not validation.get("is_valid", False):
        print(f"⏭️  [Router] Validation failed: {validation.get('error')}")
        return "reporter"
    
    print("✅ [Router] Validation passed, proceeding to scanner")
    return "scanner"


def should_proceed_to_reviewer(state: AnalysisState) -> Literal["reviewer", "reporter"]:
    """
    Decision after scanning: Did we get enough data to perform a deep forensic review?
    """
    scan_metrics = state.get("scan_metrics")
    if not scan_metrics:
        print("⏭️  [Router] No scan metrics, skipping to reporter")
        return "reporter"
    
    ncrf = scan_metrics.get("ncrf", {})
    total_sloc = ncrf.get("total_sloc", 0)
    
    if total_sloc < 10:
        print(f"⏭️  [Router] Not enough code ({total_sloc} SLOC), skipping to reporter")
        state["skip_reason"] = "Insufficient code to analyze"
        return "reporter"
    
    print(f"✅ [Router] Found {total_sloc} SLOC, proceeding to reviewer")
    return "reviewer"


def should_retry_grader(state: AnalysisState) -> Literal["grader", "judge"]:
    """
    Decision after grading: Should we retry or proceed to the Supreme Court (Judge)?
    """
    sfia_result = state.get("sfia_result")
    if not sfia_result:
        return "judge" 
    
    confidence = sfia_result.get("confidence", 1.0)
    retry_count = sfia_result.get("retry_count", 0)
    
    if confidence < 0.7 and retry_count == 0:
        print(f"🔄 [Router] Low confidence ({confidence:.2f}), retrying grader")
        state["sfia_result"]["retry_count"] = 1
        return "grader"
    
    print(f"✅ [Router] Grader finished, proceeding to Judge for final arbitration")
    return "judge"


# ============================================================================
# GRAPH DEFINITION
# ============================================================================

def create_analysis_graph():
    """Creates the LangGraph workflow with Reviewer and Judge Agents"""
    
    workflow = StateGraph(AnalysisState)
    
    # Add nodes
    workflow.add_node("validator", validate_repository)
    workflow.add_node("scanner", scan_codebase)
    workflow.add_node("reviewer", review_semantics)  # Forensic Deposition Node
    workflow.add_node("grader", grade_sfia_level)
    workflow.add_node("judge", arbitrate_level)        # The Supreme Court
    workflow.add_node("auditor", reality_check)
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
    
    # Reviewer -> Grader (Direct handoff of exhibits)
    workflow.add_edge("reviewer", "grader")
    
    # Grader -> (Retry) OR (Judge)
    workflow.add_conditional_edges(
        "grader",
        should_retry_grader,
        {
            "grader": "grader", 
            "judge": "judge"  
        }
    )
    
    # Final Adjudication Path
    workflow.add_edge("judge", "auditor")
    workflow.add_edge("auditor", "reporter")
    workflow.add_edge("reporter", END)
    
    # Compile with Memory for State Snapshots
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# Global graph instance
analysis_graph = create_analysis_graph()


# ============================================================================
# EXECUTION INTERFACE (FIXED FOR OPIK VISUALIZATION)
# ============================================================================

async def run_analysis(
    repo_url: str,
    user_id: str,
    job_id: str,
    user_github_token: str = None
) -> AnalysisState:
    """
    High-level function to run the full analysis workflow.
    Uses track_langgraph to ensure the Visual Graph appears in Opik.
    """
    
    print(f"\n{'='*70}")
    print(f"🚀 Starting SkillProtocol Analysis")
    print(f"   Job ID: {job_id}")
    print(f"   Repo: {repo_url}")
    print(f"   User: {user_id}")
    print(f"{'='*70}\n")
    
    # 1. Create Initial State
    initial_state = create_initial_state(
        repo_url=repo_url,
        user_id=user_id,
        job_id=job_id,
        user_github_token=user_github_token
    )

    # 2. Configure Opik Tracer (Minimal Config needed here)
    opik_tracer = OpikTracer(
        project_name=settings.OPIK_PROJECT_NAME,
        tags=["production", "skill-verification", "gemini-3", "langgraph"],
        metadata={
            "user_id": user_id,
            "repo_url": repo_url,
            "job_id": job_id
        }
    )
    
    # 3. CRITICAL: Wrap graph with track_langgraph
    # FIXED: Removed 'project_name' argument which caused the crash
    tracked_graph = track_langgraph(
        analysis_graph,
        opik_tracer=opik_tracer 
    )

    # 4. Configure Threading
    config = {
        "configurable": {
            "thread_id": job_id
        },
        "metadata": {
            "opik_thread_id": job_id 
        }
    }
    
    try:
        # 5. Invoke the TRACKED graph
        final_state = await tracked_graph.ainvoke(initial_state, config)
    except Exception as e:
        print(f"❌ Workflow execution error: {str(e)}")
        initial_state["errors"].append(f"Workflow error: {str(e)}")
        initial_state["current_step"] = "complete"
        initial_state["progress"] = 100
        initial_state["final_credits"] = 0.0
        return initial_state
    
    print(f"\n{'='*70}")
    print(f"✅ Analysis Complete")
    print(f"   Final Level: {final_state.get('sfia_result', {}).get('sfia_level', 'N/A')}")
    print(f"   Final Credits: {final_state.get('final_credits', 0)}")
    print(f"   Errors: {len(final_state.get('errors', []))}")
    print(f"{'='*70}\n")
    
    return final_state


async def get_analysis_status(job_id: str) -> dict:
    """Gets a snapshot of the ongoing graph state via thread_id."""
    
    config = {"configurable": {"thread_id": job_id}}
    
    try:
        # We can use the base analysis_graph for reading state (it shares memory)
        state_snapshot = await analysis_graph.aget_state(config)
        
        if not state_snapshot or not state_snapshot.values:
            return {
                "status": "not_found",
                "current_step": None,
                "progress": 0
            }
        
        values = state_snapshot.values
        
        # Determine status based on graph termination
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