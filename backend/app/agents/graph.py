import logging
from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import Opik tracking
from opik.integrations.langchain import OpikTracer, track_langgraph

# App Imports
from app.core.config import settings
from app.core.state import AnalysisState, create_initial_state

# Import agents
from app.agents.validator import validate_repository
from app.agents.scanner import scan_codebase
from app.agents.grader import grade_sfia_level
from app.agents.judge import arbitrate_level
from app.agents.auditor import reality_check
from app.agents.mentor import provide_mentorship
from app.agents.reporter import store_and_report

# Setup Logger
logger = logging.getLogger(__name__)

# ============================================================================
# NEW NODE: BAYESIAN MATH CALCULATOR
# ============================================================================

async def calculate_math_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Runs the Bayesian Math Logic using the SLOC from the Scanner.
    This ensures 'validation_result' is populated before the Grader runs.
    """
    print("🧮 [Math Node] Calculating Bayesian Priors...")
    
    scan_data = state.get("scan_metrics", {})
    ncrf_data = scan_data.get("ncrf", {})
    total_sloc = ncrf_data.get("total_sloc", 0)
    
    # 1. Define Priors (Logic: More code generally requires higher skill to manage)
    # < 2k lines = Junior (L1-2)
    # 2k - 10k = Mid (L3)
    # > 10k = Senior (L4-5)
    
    estimated_level = 1
    confidence = 0.5
    
    if total_sloc > 10000:
        estimated_level = 4
        confidence = 0.85
    elif total_sloc > 3000:
        estimated_level = 3
        confidence = 0.75
    elif total_sloc > 1000:
        estimated_level = 2
        confidence = 0.60
        
    result = {
        "validation_result": {
            "bayesian_best_estimate": estimated_level,
            "confidence": confidence,
            "details": f"Based on {total_sloc} SLOC"
        }
    }
    
    print(f"🧮 [Math Node] Result: Level {estimated_level} ({confidence*100}%)")
    return result


# ============================================================================
# ROUTING LOGIC 
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


def should_proceed_from_scanner(state: AnalysisState) -> Literal["math_model", "reporter"]:
    """
    Decision after scanning.
    Routes to 'math_model' to ensure stats are calculated before grading.
    """
    scan_metrics = state.get("scan_metrics")
    if not scan_metrics:
        print("⏭️  [Router] No scan metrics, skipping to reporter")
        return "reporter"
    
    ncrf = scan_metrics.get("ncrf", {})
    total_sloc = ncrf.get("total_sloc", 0)
    
    if total_sloc < 10:
        print(f"⏭️  [Router] Not enough code ({total_sloc} SLOC), skipping to reporter")
        return "reporter"
    
    print(f"✅ [Router] Scanner complete ({total_sloc} SLOC), proceeding to Math Model")
    return "math_model"


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
    """Decision after auditing"""
    # 1. Check if we have code analysis
    ncrf = state.get("scan_metrics", {}).get("ncrf", {})
    base_credits = ncrf.get("ncrf_base_credits", 0)
    
    if base_credits <= 0:
        print("⏭️  [Router] No measurable code found, skipping mentorship")
        return "reporter"
    
    # 2. Check Reality Check
    audit_result = state.get("audit_result", {})
    if not audit_result.get("reality_check_passed", False):
        print("⏭️  [Router] Reality check failed, skipping mentorship")
        return "reporter"

    # 3. Check SFIA ceiling
    sfia_result = state.get("sfia_result", {})
    current_level = sfia_result.get("sfia_level", 0)
    
    if current_level >= 5:
        print(f"⏭️  [Router] Expert Level {current_level}, skipping mentorship")
        return "reporter"
    
    print(f"✅ [Router] Valid Analysis (L{current_level}) -> Routing to Mentor")
    return "mentor"


# ============================================================================
# GRAPH DEFINITION 
# ============================================================================

def create_analysis_graph():
    workflow = StateGraph(AnalysisState)
    
    # Add Nodes
    workflow.add_node("validator", validate_repository)
    workflow.add_node("scanner", scan_codebase)
    workflow.add_node("math_model", calculate_math_node) # <--- NEW NODE
    workflow.add_node("grader", grade_sfia_level)
    workflow.add_node("judge", arbitrate_level)
    workflow.add_node("auditor", reality_check)
    workflow.add_node("mentor", provide_mentorship)
    workflow.add_node("reporter", store_and_report)
    
    # Entry point
    workflow.set_entry_point("validator")
    
    # Validator → Scanner
    workflow.add_conditional_edges(
        "validator",
        should_proceed_to_scanner,
        {"scanner": "scanner", "reporter": "reporter"}
    )
    
    # Scanner → Math Model (UPDATED)
    workflow.add_conditional_edges(
        "scanner",
        should_proceed_from_scanner,
        {"math_model": "math_model", "reporter": "reporter"}
    )
    
    # Math Model → Grader (NEW EDGE)
    workflow.add_edge("math_model", "grader")
    
    # Grader → (Retry) OR (Judge)
    workflow.add_conditional_edges(
        "grader",
        should_retry_grader,
        {"grader": "grader", "judge": "judge"}
    )
    
    # Judge → Auditor
    workflow.add_edge("judge", "auditor")
    
    # Auditor → Mentor
    workflow.add_conditional_edges(
        "auditor",
        should_provide_mentorship,
        {"mentor": "mentor", "reporter": "reporter"}
    )
    
    # Mentor → Reporter
    workflow.add_edge("mentor", "reporter")
    
    # Reporter → END
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
   
    print(f"\n{'='*70}")
    print(f"🚀 Starting SkillProtocol Analysis (REFACTORED)")
    print(f"   Job ID: {job_id}")
    print(f"   Repo: {repo_url}")
    print(f"   User: {user_id}")
    print(f"   Flow: 7 steps (Validator->Scanner->Math->Grader->Judge->Mentor->Reporter)")
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
        tags=["production", "refactored", "optimized"],
        metadata={
            "user_id": user_id,
            "repo_url": repo_url,
            "job_id": job_id,
            "version": "refactored_v1"
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
    print(f"✅ Analysis Complete (REFACTORED)")
    print(f"   Final Level: {final_state.get('sfia_result', {}).get('sfia_level', 'N/A')}")
    print(f"   Final Credits: {final_state.get('final_credits', 0)}")
    print(f"   Mentorship: {'Provided' if final_state.get('mentorship_plan') else 'Not applicable'}")
    print(f"   Errors: {len(final_state.get('errors', []))}")
    print(f"{'='*70}\n")
    
    return final_state


async def get_analysis_status(job_id: str) -> dict:
    """Gets a snapshot of the ongoing graph state"""
    
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