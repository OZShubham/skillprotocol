"""
Grader Agent
Uses LLM (Groq) to assign SFIA level based on scan metrics and markers
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
    1. Take scan metrics from Scanner Agent
    2. Build SFIA rubric prompt with evidence
    3. Call Groq LLM to assign SFIA level
    4. Parse and validate LLM response
    5. Check confidence threshold
    6. Retry if needed
    
    Returns:
        Updated state with sfia_result
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
        # ====================================================================
        # STEP 1: Build the SFIA Rubric Prompt
        # ====================================================================
        engine = ScoringEngine()
        ncrf_data = state["scan_metrics"]["ncrf"]
        markers = state["scan_metrics"]["markers"]
        
        # NOTE: Manual opik.track context manager removed to prevent crash
        prompt = engine.get_sfia_rubric_prompt(ncrf_data, markers)
        
        print(f"📝 [Grader Agent] Built SFIA rubric prompt ({len(prompt)} chars)")
        
        # ====================================================================
        # STEP 2: Initialize Groq Client
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
        
        print(f"🤖 [Grader Agent] Calling Groq {settings.LLM_MODEL}...")
        
        # ====================================================================
        # STEP 3: Call Groq LLM
        # ====================================================================
        try:
            # NOTE: Wrapped in main trace via @track_agent decorator
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior technical auditor specializing in SFIA (Skills Framework for the Information Age) assessments. You provide fair, evidence-based evaluations. Always respond with valid JSON only."
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
        # STEP 4: Extract and Validate Response
        # ====================================================================
        llm_response = response.choices[0].message.content
        
        if not llm_response:
            error_msg = "Groq returned empty response"
            print(f"❌ [Grader Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        print(f"✅ [Grader Agent] Received Groq response ({len(llm_response)} chars)")

        # ====================================================================
        # STEP 4.5: SAFETY GUARDRAILS (Now Working with trace())
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
            
            # If structure is invalid, log warning but continue
            if not safety_result["contains_required_fields"]:
                print(f"⚠️  [Grader Agent] LLM response missing required fields")
                print(f"   Safety checks: {safety_result}")
            
            # If PII or bias detected, log alert
            if safety_result["has_pii"] or safety_result["has_bias_language"]:
                print(f"🚨 [Grader Agent] SAFETY ALERT: {safety_result}")
                
        except Exception as e:
            print(f"⚠️  [Grader Agent] Safety check failed: {str(e)}")
            # Don't fail analysis if safety check fails
        
        # ====================================================================
        # STEP 5: Parse JSON
        # ====================================================================
        try:
            sfia_data = json.loads(llm_response)
        except json.JSONDecodeError as e:
            error_msg = f"Groq returned invalid JSON: {str(e)}"
            print(f"❌ [Grader Agent] {error_msg}")
            print(f"🔍 Raw response: {llm_response[:300]}...")
            state["errors"].append(error_msg)
            return state
        
        # Check if sfia_data is a dict
        if not isinstance(sfia_data, dict):
            error_msg = f"Groq response is not a JSON object: {type(sfia_data)}"
            print(f"❌ [Grader Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # STEP 6: Validate Required Fields
        # ====================================================================
        if "sfia_level" not in sfia_data:
            error_msg = "Groq response missing 'sfia_level' field"
            print(f"❌ [Grader Agent] {error_msg}")
            print(f"🔍 Available keys: {list(sfia_data.keys())}")
            print(f"🔍 Full response: {json.dumps(sfia_data, indent=2)}")
            state["errors"].append(error_msg)
            return state
        
        # Extract and normalize SFIA level
        raw_level = sfia_data.get("sfia_level")
        
        try:
            sfia_level = max(1, min(5, int(raw_level)))
        except (TypeError, ValueError) as e:
            error_msg = f"Invalid SFIA level format: {raw_level} ({type(raw_level).__name__})"
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
        # STEP 7: Calculate Confidence Score
        # ====================================================================
        confidence = sfia_data.get("confidence", 0.85)
        
        # Validate confidence is a number
        try:
            confidence = float(confidence)
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
        except (TypeError, ValueError):
            print(f"⚠️  [Grader Agent] Invalid confidence value: {confidence}, using 0.85")
            confidence = 0.85
        
        # Get evidence list
        evidence_list = sfia_data.get("evidence", [])
        if not isinstance(evidence_list, list):
            evidence_list = []
        
        # Lower confidence if evidence is weak
        if len(evidence_list) < 2:
            confidence *= 0.8
        
        print(f"📊 [Grader Agent] SFIA Assessment:")
        print(f"   - Level: {sfia_level} ({level_name})")
        print(f"   - Confidence: {confidence:.2%}")
        print(f"   - Evidence count: {len(evidence_list)}")
        
        # ====================================================================
        # STEP 8: Build Result
        # ====================================================================
        reasoning = sfia_data.get("reasoning", "No reasoning provided")
        missing_for_next = sfia_data.get("missing_for_next_level", [])
        
        # Ensure missing_for_next is a list
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
        
        # Log reasoning for transparency
        if reasoning and reasoning != "No reasoning provided":
            print(f"💭 Reasoning: {reasoning[:100]}...")
        
        return state
        
    except Exception as e:
        error_msg = f"Grader agent error: {str(e)}"
        print(f"❌ [Grader Agent] {error_msg}")
        
        # Print full traceback for debugging
        print(f"🔍 Traceback: {traceback.format_exc()}")
        
        state["errors"].append(error_msg)
        return state