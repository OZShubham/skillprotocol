"""
Grader Agent - UPDATED & COMPLETE (1.9.96 COMPLIANT)
Includes Native A/B Testing, Real-time Scoring, and OUTPUT GUARDRAILS for Safety.
Integrated with SSE Live Log streaming for real-time dashboard updates.
"""

import json
import traceback
import logging
from typing import Dict, Any

from openai import AsyncOpenAI
from opik import opik_context

# --- NEW IMPORT FOR GUARDRAILS ---
from opik.evaluation.metrics import Moderation

# App Imports
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent
from app.services.scoring.engine import ScoringEngine
from app.services.validation.bayesian_validator import get_validator
from app.utils.sse import push_live_log # Integrated SSE function

logger = logging.getLogger(__name__)

@track_agent(
    name="Grader Agent",
    agent_type="llm",
    tags=["sfia-assessment", "grading", "agent"]
)
async def grade_sfia_level(state: AnalysisState) -> AnalysisState:
    """
    Agent 3: Grader
    
    Responsibilities:
    1. Calculate a Bayesian Statistical Prior (The "Math").
    2. Run an A/B Test (Baseline Prompt vs. Anchored Prompt).
    3. Call the LLM to grade the code.
    4. GUARDRAIL: Check output for safety/PII before returning.
    5. Log the "Agreement Score" (LLM vs Math) directly to Opik.
    """
    
    job_id = state["job_id"]
    # 1. Update State Progress
    state["current_step"] = "grader"
    state["progress"] = get_progress_for_step("grader")
    
    print(f"🎓 [Grader Agent] Starting SFIA assessment...")
    push_live_log(job_id, "grader", "Initiating SFIA proficiency assessment...", "success")
    
    # Fail-safe check
    if not state.get("scan_metrics"):
        error_msg = "No scan metrics available for grading"
        print(f"❌ [Grader Agent] {error_msg}")
        push_live_log(job_id, "grader", "Critical error: Missing scan telemetry.", "error")
        state["errors"].append(error_msg)
        return state
    
    try:
        # 2. Prepare Engines
        engine = ScoringEngine()
        ncrf_data = state["scan_metrics"]["ncrf"]
        markers = state["scan_metrics"]["markers"]
        
        # ====================================================================
        # STEP 3: CALCULATE STATISTICAL PRIOR (The "Control")
        # ====================================================================
        print(f"🧮 [Grader Agent] Calculating Bayesian prior...")
        push_live_log(job_id, "grader", "Calculating Bayesian statistical prior from repository metrics...", "success")
        
        validator = get_validator()
        
        # This uses pure math/stats to guess the level
        statistical_hint = validator.get_statistical_suggestion(state["scan_metrics"])
        
        print(f"   ↳ Math suggests Level {statistical_hint['suggested_level']} (Confidence: {statistical_hint['confidence']:.1%})")
        push_live_log(job_id, "grader", f"Statistical baseline: Level {statistical_hint['suggested_level']} detected with {statistical_hint['confidence']:.1%} confidence.", "success")

        # Save this for the Judge later
        state["validation_result"] = {
             "bayesian_best_estimate": statistical_hint['suggested_level'],
             "confidence": statistical_hint['confidence'],
             "expected_range": statistical_hint['plausible_range'],
             "reasoning": f"Bayesian model suggests Level {statistical_hint['suggested_level']} based on metrics."
        }

        # ====================================================================
        # STEP 4: NATIVE OPIK A/B TEST (The "Experiment")
        # ====================================================================
        # We simulate an A/B test here.
        # "Variant A" = Baseline (No statistical hint given to LLM)
        # "Variant B" = Anchored (We tell the LLM what the math thinks)
        
        is_variant_b = True 
        variant_tag = "prompt_variant_b_anchored" if is_variant_b else "prompt_variant_a_baseline"
        
        # Log the experiment configuration to Opik Metadata
        experiment_config = {
            "model": settings.LLM_MODEL,
            "temperature": settings.LLM_TEMPERATURE,
            "variant": variant_tag,
            "bayesian_prior": statistical_hint['suggested_level']
        }
        
        # UPDATE OPIK CONTEXT (FIXED FOR 1.9.96)
        opik_context.update_current_trace(
            tags=[variant_tag, "production_flow"],
            metadata={
                "experiment_config": experiment_config,
                "repo_complexity": ncrf_data.get("total_complexity")
            }
        )
        
        # ====================================================================
        # STEP 5: Build Prompt
        # ====================================================================
        # If Variant B, we pass the statistical_hint. If A, we pass None.
        hint_to_pass = statistical_hint if is_variant_b else None
        
        prompt = engine.get_sfia_rubric_prompt(ncrf_data, markers, hint_to_pass)
        
        print(f"📝 [Grader Agent] Built Prompt ({len(prompt)} chars)")
        push_live_log(job_id, "grader", f"Contextual prompt constructed ({variant_tag}). Invoking technical auditor...", "success")
        
        # ====================================================================
        # STEP 6: Call LLM
        # ====================================================================
        client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        
        sfia_result_data = state.get("sfia_result") or {}  # ✅ Handle None
        retry_count = sfia_result_data.get("retry_count", 0)

        if retry_count > 0:
            print(f"🔄 [Grader Agent] Retry attempt #{retry_count}")
            push_live_log(job_id, "grader", f"Re-evaluating due to low confidence (Attempt #{retry_count})...", "warning")
        
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a senior technical auditor specializing in SFIA assessments. You provide fair, evidence-based evaluations."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=settings.LLM_TEMPERATURE,
            response_format={"type": "json_object"}
        )

        llm_response_text = response.choices[0].message.content
        
        # ====================================================================
        # STEP 6.5: OUTPUT GUARDRAILS (SAFETY LAYER)
        # ====================================================================
        # We check the LLM's response to ensure it didn't leak PII or hallucinate wild claims.
        print(f"🛡️ [Grader Agent] Running Guardrails on output...")
        push_live_log(job_id, "grader", "Running safety guardrails and moderation checks on auditor output...", "success")
        
        try:
            # We use the Opik Moderation metric as a "Safety Guard"
            guardrail = Moderation(model="groq/llama-3.3-70b-versatile")
            score_result = guardrail.score(output=llm_response_text)
            
            # If the output is flagged as unsafe/harmful (Score > 0.5 means Unsafe)
            if score_result.value > 0.5:
                print(f"🚨 [Grader Agent] Guardrail Triggered! Unsafe content detected.")
                push_live_log(job_id, "grader", "Guardrail alert: Unsafe content detected. Redacting and sanitizing output...", "error")
                
                # Log the violation to Opik for auditing (FIXED FORMAT)
                opik_context.update_current_trace(
                    tags=["guardrail_violation", "unsafe_output"],
                    metadata={
                        "guardrail_reason": score_result.reason,
                        "blocked_content_snippet": llm_response_text[:100] + "..." 
                    }
                )
                
                # Sanitization Strategy: Fallback to a safe, generic response
                llm_response_text = json.dumps({
                    "sfia_level": 1,
                    "confidence": 0.0,
                    "reasoning": "Analysis redacted due to safety content policy violation.",
                    "evidence_used": [],
                    "missing_for_next_level": []
                })
                
        except Exception as e:
            print(f"⚠️ Guardrail check failed (continuing): {e}")

        # ====================================================================
        # STEP 7: Parse & Validate
        # ====================================================================
        try:
            sfia_data = json.loads(llm_response_text)
        except json.JSONDecodeError:
            error_msg = "LLM returned invalid JSON"
            print(f"❌ [Grader Agent] {error_msg}")
            push_live_log(job_id, "grader", "Formatting error in auditor response.", "error")
            state["errors"].append(error_msg)
            return state

        # Normalize Level
        raw_level = sfia_data.get("sfia_level", 1)
        sfia_level = max(1, min(5, int(raw_level)))
        
        # Map Level Names
        level_names = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
        level_name = level_names.get(sfia_level, "Unknown")
        
        # Confidence logic
        confidence = float(sfia_data.get("confidence", 0.85))
        
        print(f"📊 [Grader Agent] Assessment: Level {sfia_level} ({level_name})")
        push_live_log(job_id, "grader", f"Proficiency Level Assigned: {sfia_level} ({level_name}). Auditor confidence: {confidence:.1%}.", "success")

        # ====================================================================
        # STEP 8: LOG EVALUATION METRIC (FIXED FOR 1.9.96)
        # ====================================================================
        # We calculate: Did the LLM agree with the Statistical Model?
        
        stats_level = statistical_hint['suggested_level']
        agreement_score = 1.0 if abs(sfia_level - stats_level) <= 1 else 0.0

        # ✅ CORRECT format for Opik 0.1.96
        opik_context.update_current_trace(
            feedback_scores=[
                {
                    "name": "bayesian_adherence", 
                    "value": float(agreement_score),
                    "category_name": "validation",  # ✅ Changed from 'category'
                    "reason": f"LLM ({sfia_level}) vs Stats ({stats_level})"
                },
                {
                    "name": "model_confidence",
                    "value": float(confidence),
                    "category_name": "quality",  # ✅ Changed from 'category'
                    "reason": "Self-reported confidence from LLM"
                }
            ]
        )

        print(f"✅ [Grader Agent] Logged Bayesian Adherence Score: {agreement_score}")

        # ====================================================================
        # STEP 9: Return State
        # ====================================================================
        new_sfia_result = {
            "sfia_level": sfia_level,
            "level_name": level_name,
            "confidence": confidence,
            "reasoning": sfia_data.get("reasoning", "No reasoning provided"),
            "evidence": sfia_data.get("evidence_used", []),
            "missing_for_next_level": sfia_data.get("missing_for_next_level", []),
            "retry_count": retry_count,
            "model_used": settings.LLM_MODEL,
            "experiment_config": experiment_config
        }
        
        state["sfia_result"] = new_sfia_result
        push_live_log(job_id, "grader", "Grading finalized. Submitting case to Supreme Court for arbitration.", "success")
        return state
        
    except Exception as e:
        error_msg = f"Grader agent error: {str(e)}"
        print(f"❌ [Grader Agent] {error_msg}")
        push_live_log(job_id, "grader", "Internal reasoning failure.", "error")
        print(traceback.format_exc())
        state["errors"].append(error_msg)
        return state