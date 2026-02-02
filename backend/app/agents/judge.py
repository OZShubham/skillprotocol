import json
import logging
from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from opik import opik_context

from app.core.config import settings
from app.core.state import AnalysisState, get_progress_for_step
from app.core.opik_config import track_agent
from app.core.prompt_manager import prompt_manager
from app.utils.sse import push_live_log

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 1. Define the Strict Schema
# ---------------------------------------------------------
class JudgeVerdict(BaseModel):
    """The exact structure the Judge MUST return."""
    final_level: int = Field(description="The final confirmed SFIA level (1-5)")
    verdict_summary: str = Field(description="A concise summary of the ruling")
    deliberation: str = Field(description="Step-by-step reasoning for the decision")
    justification: str = Field(description="Evidence-based justification for the final certificate")
    is_congruent: bool = Field(description="True if Judge agrees with the Grader, False if overruled")
    confidence_score: float = Field(description="Confidence in the verdict (0.0 to 1.0)")

@track_agent(
    name="Judge Agent", 
    agent_type="llm", 
    tags=["final-verdict", "gemini-3", "supreme-court", "openrouter"]
)
async def arbitrate_level(state: AnalysisState) -> AnalysisState:
    """
    Agent 5: Technical Judge
    Resolves conflicts using Opik Prompt Library + Structured Outputs
    """
    job_id = state["job_id"]
    state["current_step"] = "judge"
    state["progress"] = get_progress_for_step("judge")
    
    logger.info(f"[Judge] Commencing arbitration for {job_id}")
    push_live_log(job_id, "judge", "Judge impaneling: Reviewing all exhibits...", "success")
    
    # ====================================================================
    # STEP 1: GATHER COMPREHENSIVE DOSSIER (Restored Fully)
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
    
    # ====================================================================
    # STEP 2: BUILD JUDICIAL RUBRIC (Restored)
    # ====================================================================
    variables = {
        "job_id": job_id,
        "sloc": sloc,
        "learning_hours": learning_hours,
        "ncrf_credits": ncrf_credits,
        "bayesian_level": bayesian_level,
        "bayesian_confidence": f"{bayesian_confidence * 100:.1f}", 
        "bayesian_range": str(bayesian_range), 
        "llm_level": llm_level,
        "grader_reasoning": grader_reasoning,
        "witness_statement": witness_statement,
        "detailed_exhibits": detailed_exhibits
    }
    
    try:
        # ====================================================================
        # STEP 3: FETCH PROMPT FROM OPIK (Restored)
        # ====================================================================
        # This keeps your Opik Library integration active
        formatted_prompt = prompt_manager.format_prompt("judge-agent-rubric", variables)
        
        logger.info(f"[Judge] Prompt formatted from Opik Library")
        push_live_log(
            job_id,
            "judge",
            f"Deliberating: Bayesian Level {bayesian_level} vs Grader Level {llm_level}...",
            "success"
        )
        
        # ====================================================================
        # STEP 4: EXECUTE WITH STRUCTURED OUTPUT (The Fix)
        # ====================================================================
        # Instead of manual parsing, we use LangChain to force the schema
        llm = ChatOpenAI(
            model=settings.JUDGE_MODEL,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=0.1
        )
        
        structured_judge = llm.with_structured_output(JudgeVerdict)
        
        # Invoke with the prompt from Opik
        verdict: JudgeVerdict = await structured_judge.ainvoke(formatted_prompt)
        
        # ====================================================================
        # STEP 5: UPDATE STATE & LOGGING
        # ====================================================================
        final_level = max(1, min(5, verdict.final_level))
        level_names = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
        level_name = level_names.get(final_level, "Unknown")
        
        state["sfia_result"].update({
            "sfia_level": final_level,
            "level_name": level_name,
            "judge_summary": verdict.verdict_summary,
            "judge_justification": verdict.justification,
            "judge_deliberation": verdict.deliberation,
            "is_congruent": verdict.is_congruent,
            "judge_confidence": verdict.confidence_score,
            "judge_intervened": True 
        })
        
        # Log to Opik
        opik_context.update_current_trace(
            metadata={
                "judge_verdict_level": final_level,
                "is_congruent": verdict.is_congruent,
                "judicial_confidence": verdict.confidence_score,
                "deliberation_summary": verdict.deliberation[:200]
            },
            tags=[
                f"judge_level_{final_level}",
                "congruent" if verdict.is_congruent else "override",
                "judge_intervention"
            ]
        )
        
        logger.info(f"[Judge] Verdict: Level {final_level}. Congruent: {verdict.is_congruent}")
        push_live_log(job_id, "judge", f"Verdict: Level {final_level}. {verdict.verdict_summary}", "success")
        
        return state

    except Exception as e:
        # Fallback Logic
        error_msg = f"Judge Critical Error: {str(e)}"
        logger.error(f"[Judge] {error_msg}")
        push_live_log(job_id, "judge", "Judicial system failure. Defaulting to Grader.", "error")
        state["errors"].append(error_msg)
        
        # If Judge fails, we soft-fail and keep the Grader's result
        state["sfia_result"].update({
            "judge_summary": "Mistrial - Judge Unreachable",
            "judge_intervened": False
        })
        return state