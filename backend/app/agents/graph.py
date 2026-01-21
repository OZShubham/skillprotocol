"""
LangGraph Router - FIXED VERSION
Properly stops flow when validation fails
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.state import AnalysisState
from app.agents.validator import validate_repository
from app.agents.scanner import scan_codebase
from app.agents.grader import grade_sfia_level
from app.agents.auditor import reality_check
from app.agents.reporter import store_and_report
from app.agents.judge import arbitrate_level

# ============================================================================
# ROUTING LOGIC (FIXED)
# ============================================================================

def should_proceed_to_scanner(state: AnalysisState) -> Literal["scanner", "reporter"]:
    """
    Decision after validation: Should we clone and scan?
    
    FIXED: Checks both should_skip AND validation.is_valid
    """
    
    # Check skip flag
    if state.get("should_skip", False):
        print(f"⏭️  [Router] Skipping analysis: {state.get('skip_reason')}")
        return "reporter"
    
    # Check validation result
    validation = state.get("validation")
    if not validation:
        print("⏭️  [Router] No validation data, skipping to reporter")
        return "reporter"
    
    # Check is_valid flag
    if not validation.get("is_valid", False):
        print(f"⏭️  [Router] Validation failed: {validation.get('error')}")
        return "reporter"
    
    print("✅ [Router] Validation passed, proceeding to scanner")
    return "scanner"


def should_proceed_to_grader(state: AnalysisState) -> Literal["grader", "reporter"]:
    """
    Decision after scanning: Did we get enough data to grade?
    """
    
    scan_metrics = state.get("scan_metrics")
    if not scan_metrics:
        print("⏭️  [Router] No scan metrics, skipping to reporter")
        return "reporter"
    
    # Check if we have meaningful code
    ncrf = scan_metrics.get("ncrf", {})
    total_sloc = ncrf.get("total_sloc", 0)
    
    if total_sloc < 10:
        print(f"⏭️  [Router] Not enough code ({total_sloc} SLOC), skipping to reporter")
        state["skip_reason"] = "Insufficient code to analyze"
        return "reporter"
    
    print(f"✅ [Router] Found {total_sloc} SLOC, proceeding to grader")
    return "grader"


def should_retry_grader(state: AnalysisState) -> Literal["grader", "judge"]:
    """
    Decision after grading: Should we retry or proceed to judgment?
    """
    sfia_result = state.get("sfia_result")
    if not sfia_result:
        return "judge" # Always go to judge even on failure (Judge will handle empty state)
    
    confidence = sfia_result.get("confidence", 1.0)
    retry_count = sfia_result.get("retry_count", 0)
    
    # Retry logic remains, but success ALWAYS goes to Judge
    if confidence < 0.7 and retry_count == 0:
        print(f"🔄 [Router] Low confidence ({confidence:.2f}), retrying grader")
        state["sfia_result"]["retry_count"] = 1
        return "grader"
    
    print(f"✅ [Router] Grader finished, proceeding to Supreme Court (Judge)")
    return "judge"


    


# ============================================================================
# GRAPH CREATION
# ============================================================================

def create_analysis_graph():
    """Creates the LangGraph workflow with Judge Agent"""
    
    workflow = StateGraph(AnalysisState)
    
    # Add nodes
    workflow.add_node("validator", validate_repository)
    workflow.add_node("scanner", scan_codebase)
    workflow.add_node("grader", grade_sfia_level)
    workflow.add_node("judge", arbitrate_level)   # <--- Add Judge Node
    workflow.add_node("auditor", reality_check)
    workflow.add_node("reporter", store_and_report)
    
    # Entry point
    workflow.set_entry_point("validator")
    
    # Edges
    workflow.add_conditional_edges(
        "validator",
        should_proceed_to_scanner,
        {"scanner": "scanner", "reporter": "reporter"}
    )
    
    workflow.add_conditional_edges(
        "scanner",
        should_proceed_to_grader,
        {"grader": "grader", "reporter": "reporter"}
    )
    
    # Grader -> (Retry) OR (Judge)
    workflow.add_conditional_edges(
        "grader",
        should_retry_grader,
        {
            "grader": "grader", 
            "judge": "judge"  
        }
    )
    
    # Judge -> Auditor (Standard flow)
    workflow.add_edge("judge", "auditor")
    
    # Judge -> Auditor
    
    
    # Auditor -> Reporter
    workflow.add_edge("auditor", "reporter")
    
    # Reporter -> END
    workflow.add_edge("reporter", END)
    
    # Compile
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
    High-level function to run the full analysis workflow
    """
    
    from app.core.state import create_initial_state
    
    print(f"\n{'='*70}")
    print(f"🚀 Starting Analysis")
    print(f"   Job ID: {job_id}")
    print(f"   Repo: {repo_url}")
    print(f"   User: {user_id}")
    print(f"{'='*70}\n")
    
    # Create initial state
    initial_state = create_initial_state(
        repo_url=repo_url,
        user_id=user_id,
        job_id=job_id,
        user_github_token=user_github_token
    )
    
    # Run workflow
    config = {
        "configurable": {
            "thread_id": job_id
        }
    }
    
    try:
        final_state = await analysis_graph.ainvoke(initial_state, config)
    except Exception as e:
        print(f"❌ Workflow execution error: {str(e)}")
        # Return state with error
        initial_state["errors"].append(f"Workflow error: {str(e)}")
        initial_state["current_step"] = "complete"
        initial_state["progress"] = 100
        initial_state["final_credits"] = 0.0
        return initial_state
    
    print(f"\n{'='*70}")
    print(f"✅ Analysis Complete")
    print(f"   Final Credits: {final_state.get('final_credits', 0)}")
    print(f"   Errors: {len(final_state.get('errors', []))}")
    print(f"{'='*70}\n")
    
    return final_state


async def get_analysis_status(job_id: str) -> dict:
    """Get the current status of an ongoing analysis"""
    
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
        
        return {
            "status": "running" if state_snapshot.next else "complete",
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