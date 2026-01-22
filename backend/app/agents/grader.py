"""
Grader Agent - WITH EXPERIMENT TRACKING
"""

import json
import traceback
from typing import Dict, Any
from openai import AsyncOpenAI
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.services.scoring.engine import ScoringEngine

from app.core.opik_config import track_agent
from app.core.opik_advanced import OpikGuardrailMonitor
from app.services.validation.bayesian_validator import get_validator

# 🆕 NEW IMPORTS
from opik import opik_context
from app.optimization.ab_testing import log_variant_result


@track_agent(
    name="Grader Agent",
    agent_type="llm",
    tags=["sfia-assessment", "grading", "agent"]
)
async def grade_sfia_level(state: AnalysisState) -> AnalysisState:
    """
    Agent 3: Grader (WITH EXPERIMENT TRACKING)
    
    Enhancements for hackathon:
    1. Logs experiment configuration to Opik
    2. Tracks A/B test results
    3. Tags traces with prompt version
    """
    
    state["current_step"] = "grader"
    state["progress"] = get_progress_for_step("grader")
    
    print(f"🎓 [Grader Agent] Starting SFIA assessment...")
    
    if not state.get("scan_metrics"):
        error_msg = "No scan metrics available for grading"
        print(f"❌ [Grader Agent] {error_msg}")
        state["errors"].append(error_msg)
        return state
    
    try:
        engine = ScoringEngine()
        ncrf_data = state["scan_metrics"]["ncrf"]
        markers = state["scan_metrics"]["markers"]
        
        # ====================================================================
        # STEP 1: CALCULATE STATISTICAL ANCHOR (PRIOR)
        # ====================================================================
        print(f"🧮 [Grader Agent] Calculating Bayesian prior...")
        validator = get_validator()
        
        statistical_hint = validator.get_statistical_suggestion(state["scan_metrics"])
        
        print(f"   ↳ Math suggests Level {statistical_hint['suggested_level']} (Confidence: {statistical_hint['confidence']:.1%})")

        state["validation_result"] = {
             "bayesian_best_estimate": statistical_hint['suggested_level'],
             "confidence": statistical_hint['confidence'],
             "expected_range": statistical_hint['plausible_range'],
             "reasoning": f"Bayesian model suggests Level {statistical_hint['suggested_level']} based on metrics."
        }

        # ====================================================================
        # 🆕 STEP 1.5: LOG EXPERIMENT CONFIGURATION
        # ====================================================================
        experiment_config = {
            "model": settings.LLM_MODEL,
            "temperature": settings.LLM_TEMPERATURE,
            "prompt_version": "v2.1-bayesian-anchored",
            "statistical_hint_enabled": True,
            "bayesian_prior": statistical_hint['suggested_level']
        }
        
        # Update current trace with experiment metadata
        opik_context.update_current_trace(
            tags=[
                "production",
                f"model:{settings.LLM_MODEL}",
                f"prompt:v2.1",
                "bayesian-anchored",
                "ab-test-variant-b"  # This is variant B (with anchoring)
            ],
            metadata={
                "experiment": experiment_config,
                "statistical_prior": statistical_hint,
                "repo_complexity": ncrf_data.get("total_complexity")
            }
        )
        
        # ====================================================================
        # STEP 2: Build the SFIA Rubric Prompt (With Anchor)
        # ====================================================================
        prompt = engine.get_sfia_rubric_prompt(ncrf_data, markers, statistical_hint)
        
        print(f"📝 [Grader Agent] Built Anchored Prompt ({len(prompt)} chars)")
        
        # ====================================================================
        # STEP 3: Initialize Groq Client
        # ====================================================================
        client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        
        sfia_result = state.get("sfia_result")
        retry_count = 0
        if sfia_result and isinstance(sfia_result, dict):
            retry_count = sfia_result.get("retry_count", 0)
        
        if retry_count > 0:
            print(f"🔄 [Grader Agent] Retry attempt #{retry_count}")
        
        print(f"🤖 [Grader Agent] Asking LLM to review evidence against statistical prior...")
        
        # ====================================================================
        # STEP 4: Call Groq LLM
        # ====================================================================
        try:
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior technical auditor specializing in SFIA assessments. You provide fair, evidence-based evaluations. Use the provided statistical prior as a baseline."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.LLM_TEMPERATURE,
                response_format={"type": "json_object"}
            )

        except Exception as api_error:
            error_msg = f"Groq API call failed: {str(api_error)}"
            print(f"❌ [Grader Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # STEP 5: Extract and Validate Response
        # ====================================================================
        llm_response = response.choices[0].message.content
        
        if not llm_response:
            error_msg = "Groq returned empty response"
            print(f"❌ [Grader Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        print(f"✅ [Grader Agent] Received Groq response ({len(llm_response)} chars)")

        # ====================================================================
        # STEP 5.5: SAFETY GUARDRAILS
        # ====================================================================
        try:
            guardrails = OpikGuardrailMonitor()
            safety_result = guardrails.check_response_safety(
                llm_response=llm_response,
                context={
                    "repo_url": state.get("repo_url", "Unknown"),
                    "user_id": state.get("user_id", "Unknown"),
                    "job_id": state.get("job_id", "Unknown")
                }
            )
            
            if not safety_result["contains_required_fields"]:
                print(f"⚠️  [Grader Agent] LLM response missing required fields")
            
            if safety_result["has_pii"] or safety_result["has_bias_language"]:
                print(f"🚨 [Grader Agent] SAFETY ALERT: {safety_result}")
                
        except Exception as e:
            print(f"⚠️  [Grader Agent] Safety check failed: {str(e)}")
        
        # ====================================================================
        # STEP 6: Parse JSON
        # ====================================================================
        try:
            sfia_data = json.loads(llm_response)
        except json.JSONDecodeError as e:
            error_msg = f"Groq returned invalid JSON: {str(e)}"
            print(f"❌ [Grader Agent] {error_msg}")
            print(f"🔍 Raw response: {llm_response[:300]}...")
            state["errors"].append(error_msg)
            return state
        
        if not isinstance(sfia_data, dict):
            error_msg = f"Groq response is not a JSON object: {type(sfia_data)}"
            print(f"❌ [Grader Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # STEP 7: Validate Required Fields
        # ====================================================================
        if "sfia_level" not in sfia_data:
            error_msg = "Groq response missing 'sfia_level' field"
            print(f"❌ [Grader Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # Extract and normalize SFIA level
        raw_level = sfia_data.get("sfia_level")
        
        try:
            sfia_level = max(1, min(5, int(raw_level)))
        except (TypeError, ValueError) as e:
            error_msg = f"Invalid SFIA level format: {raw_level}"
            print(f"❌ [Grader Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # Map level to name
        level_names = {
            1: "Follow",
            2: "Assist", 
            3: "Apply",
            4: "Enable",
            5: "Ensure"
        }
        level_name = level_names.get(sfia_level, "Unknown")
        
        # ====================================================================
        # STEP 8: Calculate Confidence Score
        # ====================================================================
        confidence = sfia_data.get("confidence", 0.85)
        try:
            confidence = float(confidence)
            confidence = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            confidence = 0.85
        
        evidence_list = sfia_data.get("evidence", [])
        if not isinstance(evidence_list, list):
            evidence_list = []
        
        if len(evidence_list) < 2:
            confidence *= 0.8
        
        print(f"📊 [Grader Agent] SFIA Assessment:")
        print(f"   - Level: {sfia_level} ({level_name})")
        print(f"   - Confidence: {confidence:.2%}")
        
        # ====================================================================
        # 🆕 STEP 8.5: LOG A/B TEST RESULT
        # ====================================================================
        llm_level = sfia_level
        stats_level = statistical_hint['suggested_level']
        agreement = abs(llm_level - stats_level) <= 1  # Within 1 level = agreement
        
        # Log to A/B testing framework
        log_variant_result(
            experiment_name="bayesian-anchoring-v2",
            variant="b",  # This is the "anchored" variant
            result={
                "llm_level": llm_level,
                "bayesian_level": stats_level,
                "agreement": agreement,
                "confidence": confidence,
                "job_id": state.get("job_id")
            }
        )
        
        print(f"📊 [Grader Agent] A/B Test logged: Agreement={agreement}")
        
        # ====================================================================
        # STEP 9: Build Result
        # ====================================================================
        reasoning = sfia_data.get("reasoning", "No reasoning provided")
        missing_for_next = sfia_data.get("missing_for_next_level", [])
        if not isinstance(missing_for_next, list):
            missing_for_next = []
        
        new_sfia_result = {
            "sfia_level": sfia_level,
            "level_name": level_name,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": evidence_list,
            "missing_for_next_level": missing_for_next,
            "retry_count": retry_count,
            "model_used": settings.LLM_MODEL,
            # 🆕 Add experiment metadata
            "experiment_config": experiment_config
        }
        
        state["sfia_result"] = new_sfia_result
        
        print(f"✅ [Grader Agent] Assessment complete")
        
        if reasoning and reasoning != "No reasoning provided":
            print(f"💭 Reasoning: {reasoning[:100]}...")
        
        return state
        
    except Exception as e:
        error_msg = f"Grader agent error: {str(e)}"
        print(f"❌ [Grader Agent] {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        state["errors"].append(error_msg)
        return state