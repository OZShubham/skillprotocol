
import json
import logging
from typing import Dict, Any

from opik import opik_context

from app.core.config import settings
from app.core.state import AnalysisState, get_progress_for_step
from app.core.opik_config import track_agent
from app.core.prompt_manager import prompt_manager
from app.utils.sse import push_live_log

logger = logging.getLogger(__name__)

@track_agent(name="Judge Agent", agent_type="llm", tags=["final-verdict", "gemini-3", "supreme-court"])
async def arbitrate_level(state: AnalysisState) -> AnalysisState:
    """
    Agent 5: Technical Judge )
    
    Responsibilities:
    1. Reconcile Bayesian Math, Grader verdict, and Reviewer forensics
    2. Apply the "Congruence Rule" and "Quantum Verification"
    3. Issue final binding verdict
    4. Generate justification for certificate
    """
    
    job_id = state["job_id"]
    state["current_step"] = "judge"
    state["progress"] = get_progress_for_step("judge")
    
    logger.info(f"[Judge] Commencing arbitration for {job_id}")
    push_live_log(job_id, "judge", "Judge impaneling: Reviewing all exhibits...", "success")
    
    # ====================================================================
    # STEP 1: GATHER COMPREHENSIVE DOSSIER
    # ====================================================================
    ncrf = state.get("scan_metrics", {}).get("ncrf", {})
    sfia = state.get("sfia_result", {})
    stats = state.get("validation_result", {})
    sem = state.get("semantic_report", {})
    
    # Extract key data
    bayesian_level = stats.get("bayesian_best_estimate", 3)
    bayesian_confidence = stats.get("confidence", 0.0)
    bayesian_range = stats.get("expected_range", [bayesian_level])
    
    llm_level = sfia.get("sfia_level", 3)
    grader_reasoning = sfia.get("reasoning", "No reasoning provided")
    
    witness_statement = sem.get("final_witness_statement", "No forensic testimony available.")
    detailed_exhibits = json.dumps(sem.get("exhibits", {}), indent=2)
    
    sloc = ncrf.get("total_sloc", 0)
    learning_hours = ncrf.get("estimated_learning_hours", 0)
    ncrf_credits = ncrf.get("ncrf_base_credits", 0.0)
    
    # Log dossier summary
    logger.info(
        f"[Judge] Dossier: Bayesian={bayesian_level}, Grader={llm_level}, "
        f"SLOC={sloc}, Hours={learning_hours}"
    )
    
    # ====================================================================
    # STEP 2: BUILD JUDICIAL RUBRIC WITH EXACT OPIK TEMPLATE VARIABLES
    # ====================================================================
    variables = {
        "job_id": job_id,
        "sloc": sloc,
        "learning_hours": learning_hours,
        "ncrf_credits": ncrf_credits,
        "bayesian_level": bayesian_level,
        "bayesian_confidence": f"{bayesian_confidence * 100:.1f}",  # Convert to percentage string
        "bayesian_range": str(bayesian_range),  # Convert list to string for template
        "llm_level": llm_level,
        "grader_reasoning": grader_reasoning,
        "witness_statement": witness_statement,
        "detailed_exhibits": detailed_exhibits
    }
    
    try:
        # ====================================================================
        # STEP 3: FETCH JUDICIAL RUBRIC FROM OPIK
        # ====================================================================
        formatted_prompt = prompt_manager.format_prompt("judge-agent-rubric", variables)
        
        logger.info(f"[Judge] Prompt formatted, invoking Gemini 3 Flash")
        push_live_log(
            job_id,
            "judge",
            f"Deliberating: Bayesian Level {bayesian_level} vs Grader Level {llm_level}...",
            "success"
        )
        
        # ====================================================================
        # STEP 4: EXECUTE ARBITRATION VIA GEMINI 3 FLASH (MEDIUM THINKING)
        # ====================================================================
        raw_response = await prompt_manager.call_gemini(
            prompt_text=formatted_prompt,
            thinking_level="medium"  # Deep deliberation for complex cases
        )
        
        # Parse verdict
        verdict = json.loads(raw_response)
        
        # Validate required fields
        required_fields = [
            "deliberation",
            "final_level",
            "is_congruent",
            "verdict_summary",
            "justification",
            "confidence_score"
        ]
        
        for field in required_fields:
            if field not in verdict:
                raise ValueError(f"Judge response missing required field: {field}")
        
        # ====================================================================
        # STEP 5: EXTRACT AND NORMALIZE VERDICT
        # ====================================================================
        final_level = int(verdict.get("final_level", llm_level))
        final_level = max(1, min(5, final_level))  # Ensure 1-5 range
        
        is_congruent = bool(verdict.get("is_congruent", True))
        confidence_score = float(verdict.get("confidence_score", 0.8))
        
        level_names = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
        level_name = level_names.get(final_level, "Unknown")
        
        # ====================================================================
        # STEP 6: UPDATE STATE WITH JUDGE VERDICT
        # ====================================================================
        state["sfia_result"].update({
            "sfia_level": final_level,
            "level_name": level_name,
            "judge_summary": verdict.get("verdict_summary"),
            "judge_justification": verdict.get("justification"),
            "judge_deliberation": verdict.get("deliberation"),
            "is_congruent": is_congruent,
            "judge_confidence": confidence_score,
            "judge_intervened": True  # Flag that judge made the final call
        })
        
        # ====================================================================
        # STEP 7: LOG JUDICIAL METRICS TO OPIK
        # ====================================================================
        opik_context.update_current_trace(
            metadata={
                "judge_verdict_level": final_level,
                "is_congruent": is_congruent,
                "judicial_confidence": confidence_score,
                "bayesian_vs_grader_delta": abs(bayesian_level - llm_level),
                "judge_vs_grader_delta": abs(final_level - llm_level),
                "deliberation_summary": verdict["deliberation"]
            },
            tags=[
                f"judge_level_{final_level}",
                "congruent" if is_congruent else "override",
                "judge_intervention"
            ]
        )
        
        # ====================================================================
        # STEP 8: LOG SUCCESS
        # ====================================================================
        logger.info(
            f"[Judge] Verdict: Level {final_level} ({level_name}). "
            f"Congruent: {is_congruent}, Confidence: {confidence_score:.1%}"
        )
        
        push_live_log(
            job_id,
            "judge",
            f"Final Verdict: Level {final_level} ({level_name}). "
            f"Reasoning: {verdict['verdict_summary'][:800]}...",
            "success"
        )
        
        return state
        
    except json.JSONDecodeError as e:
        error_msg = f"Judge failed to parse Gemini response: {str(e)}"
        logger.error(f"[Judge] {error_msg}")
        push_live_log(job_id, "judge", "Verdict parsing failed. Defaulting to Grader.", "error")
        
        state["errors"].append(error_msg)
        
        # Fallback: Keep Grader's verdict
        state["sfia_result"].update({
            "judge_summary": "Mistrial - Judge parsing error",
            "judge_justification": f"Error: {str(e)}. Defaulting to Grader verdict.",
            "judge_intervened": False
        })
        
        return state
        
    except Exception as e:
        error_msg = f"Judge critical failure: {str(e)}"
        logger.error(f"[Judge] {error_msg}")
        push_live_log(job_id, "judge", "Internal judicial error. Defaulting to Grader.", "error")
        
        state["errors"].append(error_msg)
        
        # ✅ FIX: Lower confidence on failure
        state["sfia_result"].update({
            "judge_summary": "Mistrial - Internal error",
            "judge_justification": f"Error: {str(e)}. Grader verdict stands.",
            "judge_intervened": False,
            "judge_confidence": 0.5  # ✅ Lower confidence on error
        })
        
        return state

# def _get_level_name(level: int) -> str:
#     """Helper to get SFIA level name"""
#     mapping = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
#     return mapping.get(int(level or 0), "Unknown")