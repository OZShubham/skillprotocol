"""
Grader Agent
Uses LLM (Groq) to assign SFIA level based on scan metrics and markers.
Now includes 'Statistical Anchoring' to reduce hallucinations.
"""

import json
import traceback
from typing import Dict, Any
from openai import AsyncOpenAI
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.services.scoring.engine import ScoringEngine

# Imports
from app.core.opik_config import track_agent
from app.core.opik_advanced import OpikGuardrailMonitor

# --- NEW IMPORT ---
from app.services.validation.bayesian_validator import get_validator

# Decorator
@track_agent(
    name="Grader Agent",
    agent_type="llm",
    tags=["sfia-assessment", "grading", "agent"]
)
async def grade_sfia_level(state: AnalysisState) -> AnalysisState:
    """
    Agent 3: Grader
    
    Responsibilities:
    1. Calculate Bayesian Prior (Statistical Anchor)
    2. Build SFIA prompt (Anchored with stats)
    3. Call Groq LLM
    4. Save BOTH results for the Judge
    """
    
    # Update progress
    state["current_step"] = "grader"
    state["progress"] = get_progress_for_step("grader")
    
    print(f"🎓 [Grader Agent] Starting SFIA assessment...")
    
    # Check if we have scan metrics
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
        
        # Get purely statistical suggestion based on metrics
        # NOTE: Ensure you added 'get_statistical_suggestion' to bayesian_validator.py
        statistical_hint = validator.get_statistical_suggestion(state["scan_metrics"])
        
        print(f"   ↳ Math suggests Level {statistical_hint['suggested_level']} (Confidence: {statistical_hint['confidence']:.1%})")

        # IMPORTANT: Save this to state so the Judge Agent can see it later!
        state["validation_result"] = {
             "bayesian_best_estimate": statistical_hint['suggested_level'],
             "confidence": statistical_hint['confidence'],
             "expected_range": statistical_hint['plausible_range'],
             "reasoning": f"Bayesian model suggests Level {statistical_hint['suggested_level']} based on metrics."
        }

        # ====================================================================
        # STEP 2: Build the SFIA Rubric Prompt (With Anchor)
        # ====================================================================
        # We pass the hint to the engine to create the "Anchored" prompt
        # NOTE: Ensure 'get_sfia_rubric_prompt' in engine.py accepts this arg
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
            # NOTE: Wrapped in main trace via @track_agent decorator
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
            "model_used": settings.LLM_MODEL
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