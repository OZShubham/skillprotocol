"""
Grader Agent 
Performs initial SFIA assessment using statistical anchoring and forensic exhibits.
"""

import json
import traceback
import logging
from typing import Dict, Any

from openai import AsyncOpenAI
from opik import opik_context
from opik.evaluation.metrics import Moderation

from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent
from app.core.prompt_manager import prompt_manager
from app.services.scoring.engine import ScoringEngine
from app.services.validation.bayesian_validator import get_validator
from app.utils.sse import push_live_log

logger = logging.getLogger(__name__)

@track_agent(
    name="Grader Agent",
    agent_type="llm",
    tags=["sfia-assessment", "grading", "grok"]
)
async def grade_sfia_level(state: AnalysisState) -> AnalysisState:
    """
    Agent 4: Grader (Initial Assessor using Grok)
    
    Responsibilities:
    1. Calculate Bayesian Statistical Prior
    2. Fetch SFIA grading prompt from Opik (if exists) or use engine fallback
    3. Call Grok LLM with statistical anchoring + forensic exhibits
    4. Apply output guardrails (Moderation)
    5. Log agreement score (LLM vs Bayesian Math)
    """
    
    job_id = state["job_id"]
    state["current_step"] = "grader"
    state["progress"] = get_progress_for_step("grader")
    
    logger.info(f"[Grader] Starting assessment for {job_id}")
    push_live_log(job_id, "grader", "Initiating SFIA proficiency assessment...", "success")
    
    # Validation check
    scan_metrics = state.get("scan_metrics")
    if not scan_metrics:
        error_msg = "No scan metrics available for grading"
        logger.error(f"[Grader] {error_msg}")
        push_live_log(job_id, "grader", "Critical error: Missing scan telemetry.", "error")
        state["errors"].append(error_msg)
        return state
    
    try:
        # Extract data
        ncrf_data = scan_metrics["ncrf"]
        markers = scan_metrics["markers"]
        semantic_report = state.get("semantic_report", {})
        
        # ====================================================================
        # STEP 1: CALCULATE STATISTICAL PRIOR (Bayesian Math)
        # ====================================================================
        logger.info(f"[Grader] Calculating Bayesian prior for {job_id}")
        push_live_log(job_id, "grader", "Calculating Bayesian statistical prior...", "success")
        
        validator = get_validator()
        statistical_hint = validator.get_statistical_suggestion(scan_metrics)
        
        # Store in state for Judge
        state["validation_result"] = {
            "bayesian_best_estimate": statistical_hint['suggested_level'],
            "confidence": statistical_hint['confidence'],
            "expected_range": statistical_hint['plausible_range'],
            "reasoning": f"Bayesian model suggests Level {statistical_hint['suggested_level']} based on metrics."
        }
        
        logger.info(
            f"[Grader] Bayesian suggests Level {statistical_hint['suggested_level']} "
            f"({statistical_hint['confidence']:.1%} confidence)"
        )
        push_live_log(
            job_id, 
            "grader", 
            f"Statistical baseline: Level {statistical_hint['suggested_level']} "
            f"with {statistical_hint['confidence']:.1%} confidence.",
            "success"
        )
        
        # ====================================================================
        # STEP 2: BUILD PROMPT WITH STATISTICAL ANCHORING
        # ====================================================================
        # Try to fetch from Opik first, fallback to engine.py
        try:
            # Check if prompt exists in Opik library
            prompt_text = prompt_manager.format_prompt(
                "sfia-grader-v2",
                {
                    "total_sloc": ncrf_data.get("total_sloc", 0),
                    "complexity": ncrf_data.get("total_complexity", 0),
                    "learning_hours": ncrf_data.get("estimated_learning_hours", 0),
                    "ci_cd_found": markers.get("has_ci_cd", False),
                    "tests_found": markers.get("has_tests", False),
                    "witness_deposition": semantic_report.get("deposition_summary", "No forensic summary available."),
                    "forensic_exhibits": json.dumps(semantic_report.get("exhibits", {}), indent=2),
                    "bayesian_hint": statistical_hint['suggested_level']
                }
            )
            logger.info(f"[Grader] Using Opik prompt library")
        except Exception as e:
            logger.warning(f"[Grader] Opik prompt fetch failed ({e}), using engine fallback")
            engine = ScoringEngine()
            
            # ✅ Build prompt with semantic context
            base_prompt = engine.get_sfia_rubric_prompt(
                ncrf_stats=ncrf_data,
                markers=markers,
                statistical_hint=statistical_hint
            )
            
            # ✅ ADD: Append forensic deposition if available
            semantic_report = state.get("semantic_report", {})
            if semantic_report:
                deposition = semantic_report.get("deposition_summary", "")
                exhibits = json.dumps(semantic_report.get("exhibits", {}), indent=2)
                
                forensic_addendum = f"""

                    **🔬 FORENSIC ARCHITECT'S DEPOSITION:**
                    {deposition}

                    **DETAILED EXHIBITS:**
                    {exhibits}
            """
                prompt_text = base_prompt + forensic_addendum
            else:
                prompt_text = base_prompt
        
        push_live_log(job_id, "grader", "Contextual prompt constructed. Invoking Grok assessor...", "success")
        
        # ====================================================================
        # STEP 3: CALL GROK LLM
        # ====================================================================
        client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY, 
            base_url=settings.LLM_BASE_URL
        )
        
        # Check for retries
        sfia_result_data = state.get("sfia_result") or {}
        retry_count = sfia_result_data.get("retry_count", 0)
        
        if retry_count > 0:
            logger.info(f"[Grader] Retry attempt #{retry_count}")
            push_live_log(job_id, "grader", f"Re-evaluating (Attempt #{retry_count})...", "warning")
        
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior technical auditor specializing in SFIA assessments. "
                               "You provide fair, evidence-based evaluations in strict JSON format."
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ],
            temperature=settings.LLM_TEMPERATURE,
            response_format={"type": "json_object"}
        )
        
        llm_response_text = response.choices[0].message.content
        
        # ====================================================================
        # STEP 4: OUTPUT GUARDRAILS (Safety Check)
        # ====================================================================
        logger.info(f"[Grader] Running output guardrails")
        push_live_log(job_id, "grader", "Running safety guardrails on output...", "success")
        
        try:
            guardrail = Moderation(model="groq/llama-3.3-70b-versatile")
            score_result = guardrail.score(output=llm_response_text)
            
            if score_result.value > 0.5:
                logger.warning(f"[Grader] Guardrail triggered for {job_id}")
                push_live_log(job_id, "grader", "Guardrail alert: Unsafe content detected.", "error")
                
                opik_context.update_current_trace(
                    tags=["guardrail_violation", "unsafe_output"],
                    metadata={
                        "guardrail_reason": score_result.reason,
                        "blocked_snippet": llm_response_text[:100] + "..."
                    }
                )
                
                # Return safe fallback
                llm_response_text = json.dumps({
                    "sfia_level": 1,
                    "confidence": 0.0,
                    "reasoning": "Analysis redacted due to safety policy violation.",
                    "evidence_used": [],
                    "missing_for_next_level": []
                })
        except Exception as e:
            logger.warning(f"[Grader] Guardrail check failed (continuing): {e}")
        
        # ====================================================================
        # STEP 5: PARSE AND VALIDATE
        # ====================================================================
        try:
            sfia_data = json.loads(llm_response_text)
        except json.JSONDecodeError as e:
            error_msg = f"Grok returned invalid JSON: {str(e)}"
            logger.error(f"[Grader] {error_msg}")
            push_live_log(job_id, "grader", "Formatting error in assessor response.", "error")
            state["errors"].append(error_msg)
            return state
        
        # Extract and normalize level
        raw_level = sfia_data.get("sfia_level", 1)
        sfia_level = max(1, min(5, int(raw_level)))
        
        level_names = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
        level_name = level_names.get(sfia_level, "Unknown")
        confidence = float(sfia_data.get("confidence", 0.85))
        
        logger.info(f"[Grader] Assessment: Level {sfia_level} ({level_name}) @ {confidence:.1%} confidence")
        push_live_log(
            job_id,
            "grader",
            f"Level {sfia_level} ({level_name}) assigned. Confidence: {confidence:.1%}",
            "success"
        )
        
        # ====================================================================
        # STEP 6: LOG BAYESIAN AGREEMENT METRIC
        # ====================================================================
        stats_level = statistical_hint['suggested_level']
        agreement_score = 1.0 if abs(sfia_level - stats_level) <= 1 else 0.0
        
        opik_context.update_current_trace(
            feedback_scores=[
                {
                    "name": "bayesian_adherence",
                    "value": float(agreement_score),
                    "category_name": "validation",
                    "reason": f"LLM ({sfia_level}) vs Bayesian ({stats_level})"
                },
                {
                    "name": "model_confidence",
                    "value": float(confidence),
                    "category_name": "quality",
                    "reason": "Grok self-reported confidence"
                }
            ]
        )
        
        # ====================================================================
        # STEP 7: UPDATE STATE
        # ====================================================================
        state["sfia_result"] = {
            "sfia_level": sfia_level,
            "level_name": level_name,
            "confidence": confidence,
            "reasoning": sfia_data.get("reasoning", "No reasoning provided"),
            "evidence": sfia_data.get("evidence_used", []),
            "missing_for_next_level": sfia_data.get("missing_for_next_level", []),
            "retry_count": retry_count,
            "model_used": settings.LLM_MODEL,
            "statistical_prior": stats_level,
            "bayesian_agreement": agreement_score
        }
        
        logger.info(f"[Grader] Complete. Bayesian adherence: {agreement_score}")
        push_live_log(job_id, "grader", "Assessment finalized. Submitting to Judge.", "success")
        
        return state
        
    except Exception as e:
        error_msg = f"Grader critical failure: {str(e)}"
        logger.error(f"[Grader] {error_msg}\n{traceback.format_exc()}")
        push_live_log(job_id, "grader", "Internal reasoning failure.", "error")
        state["errors"].append(error_msg)
        return state