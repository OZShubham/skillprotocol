"""
Reporter Agent - SUPREME COURT COMPATIBLE
Respects Judge's verdicts, calculates final scores, and logs immutable proof to Opik.
"""

from datetime import datetime
import logging
from typing import Dict, Any, List

# Native Opik Imports
from opik import opik_context

# App Imports
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent, log_to_main_project
# REMOVED: Unused OpikQualityDashboard and get_git_analyzer imports
from app.services.validation.bayesian_validator import get_validator

# Initialize logger
logger = logging.getLogger(__name__)

@track_agent(
    name="Reporter Agent",
    agent_type="tool",
    tags=["final-scoring", "reporting", "agent"]
)
async def store_and_report(state: AnalysisState) -> AnalysisState:
    """
    Agent 5: Reporter
    
    Responsibilities:
    1. Capture the authoritative Opik Trace ID.
    2. Resolve conflicts between Judge and Bayesian Validator.
    3. Calculate final credits.
    4. Save to database.
    5. Log feedback scores to Opik.
    """
    
    # 1. Update Progress
    state["current_step"] = "reporter"
    state["progress"] = get_progress_for_step("reporter")
    
    print(f"📝 [Reporter Agent] Finalizing analysis...")

    try:
        # ====================================================================
        # STEP 0: CAPTURE OPIK TRACE ID
        # ====================================================================
        try:
            current_trace = opik_context.get_current_trace_data()
            if current_trace:
                state["opik_trace_id"] = current_trace.id
                print(f"🔗 [Reporter Agent] Linked to Opik Trace: {current_trace.id}")
        except Exception as e:
            print(f"⚠️ [Reporter Agent] Could not capture trace context: {e}")

        # ====================================================================
        # STEP 1: Validation Check
        # ====================================================================
        validation = state.get("validation")
        
        if not validation or not validation.get("is_valid"):
            print(f"⚠️  [Reporter Agent] Validation failed. Generating error report.")
            
            certificate = {
                "repo_url": state.get("repo_url", "Unknown"),
                "credits_awarded": 0.0,
                "error": True,
                "error_reason": validation.get("error") if validation else "Validation failed",
                "issued_at": datetime.utcnow().isoformat(),
                "verification_id": state.get("job_id")
            }
            
            state["final_credits"] = 0.0
            state["certificate"] = certificate
            state["current_step"] = "complete"
            state["progress"] = 100
            state["completed_at"] = datetime.utcnow().isoformat()
            
            return state

        # ====================================================================
        # STEP 2: Calculate Final Credits
        # ====================================================================
        final_credits = _calculate_final_credits(state)
        state["final_credits"] = final_credits
        
        print(f"💳 [Reporter Agent] Final credits calculated: {final_credits:.2f}")

        # ====================================================================
        # STEP 3: Judge vs. Math Synchronization
        # ====================================================================
        validation_result = state.get("validation_result")
        sfia_result = state.get("sfia_result", {})
        
        # Check if Judge Intervened (The "Supreme Court" Check)
        if sfia_result.get("judge_intervened"):
            print(f"⚖️ [Reporter Agent] Supreme Court ruled on this case.")
            
            # If Judge resolved the conflict, downgrade the statistical alert
            if validation_result and validation_result.get("alert"):
                print("   ↳ Clearing statistical alert (Judge verdict takes precedence)")
                validation_result["alert"] = False
                validation_result["reasoning"] += " [OVERRULED BY JUDGE]"

        # Fallback: Run Bayesian check if missing (e.g., if Grader crashed but we continued)
        elif not validation_result and state.get("scan_metrics"):
            try:
                print(f"🔬 [Reporter Agent] Running late-bound Bayesian validation...")
                # We read git stability from STATE, not disk (since repo is deleted)
                git_stability = await _get_git_stability(state)
                validator = get_validator()
                
                validation_result = validator.validate_assessment(
                    predicted_level=state["sfia_result"].get("sfia_level", 3),
                    metrics=state["scan_metrics"],
                    git_stability=git_stability
                )
                state["validation_result"] = validation_result
            except Exception as e:
                print(f"⚠️ [Reporter Agent] Bayesian fallback failed: {e}")

        # ====================================================================
        # STEP 4: Database Persistence
        # ====================================================================
        print(f"💾 [Reporter Agent] Saving to database...")
        try:
            from app.models.database import save_analysis_result
            await save_analysis_result(state)
            print(f"✅ [Reporter Agent] Saved to database")
        except Exception as e:
            print(f"⚠️ [Reporter Agent] Database save failed (Non-fatal): {str(e)}")
            state["errors"].append(f"Database save failed: {str(e)}")

        # ====================================================================
        # STEP 5: Generate Final Certificate
        # ====================================================================
        certificate = _generate_certificate(state, validation_result)
        state["certificate"] = certificate

        # ====================================================================
        # STEP 6: Log Native Opik Metrics
        # ====================================================================
        # Around line 220-280 in reporter.py
        try:
            feedback_scores = []
            
            # 1. SFIA Confidence
            if sfia_result.get("confidence"):
                feedback_scores.append({
                    "name": "sfia_confidence",
                    "value": float(sfia_result["confidence"]),
                    "category_name": "quality",  # ✅ Changed from 'category'
                    "reason": f"LLM confidence in SFIA level assessment"
                })
            
            # 2. Bayesian Confidence
            if validation_result and validation_result.get("confidence"):
                feedback_scores.append({
                    "name": "bayesian_confidence",
                    "value": float(validation_result["confidence"]),
                    "category_name": "quality",  # ✅ Changed from 'category'
                    "reason": f"Statistical model confidence in prediction"
                })

            # 3. Reality Check (Binary)
            audit_passed = audit_result_passed(state)
            feedback_scores.append({
                "name": "reality_check_passed",
                "value": 1.0 if audit_passed else 0.0,
                "category_name": "compliance",  # ✅ Changed from 'category'
                "reason": "CI/CD tests passed" if audit_passed else "CI/CD tests failed or not present"
            })

            # 4. Final Credits
            feedback_scores.append({
                "name": "credits_awarded",
                "value": float(final_credits),
                "category_name": "business",  # ✅ Changed from 'category'
                "reason": f"Total verified skill credits calculated"
            })

            # Update the Trace
            opik_context.update_current_trace(
                feedback_scores=feedback_scores,
                tags=[
                    f"sfia_level_{sfia_result.get('sfia_level', 0)}",
                    "verified" if audit_passed else "audit_failed",
                    "judge_intervention" if sfia_result.get("judge_intervened") else "standard_flow"
                ],
                metadata={
                    "repo_url": state.get("repo_url"),
                    "final_credits": final_credits,
                    "sfia_level": sfia_result.get("sfia_level"),
                    "judge_ruling": sfia_result.get("judge_ruling")
                }
            )

            print(f"✅ [Reporter Agent] Native Feedback Scores pushed to Opik")
            
        except Exception as e:
            print(f"⚠️ [Reporter Agent] Opik metrics logging failed: {str(e)}")

        # ====================================================================
        # STEP 7: Completion
        # ====================================================================
        state["current_step"] = "complete"
        state["progress"] = 100
        state["completed_at"] = datetime.utcnow().isoformat()
        
        _print_summary(state, validation_result)
        
        return state

    except Exception as e:
        error_msg = f"Reporter agent critical failure: {str(e)}"
        print(f"❌ [Reporter Agent] {error_msg}")
        state["errors"].append(error_msg)
        state["final_credits"] = 0.0
        state["current_step"] = "complete"
        state["progress"] = 100
        return state


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def audit_result_passed(state: AnalysisState) -> bool:
    """Helper to check if auditor passed"""
    audit = state.get("audit_result", {})
    if not audit: return False
    return audit.get("reality_check_passed", False)

def _calculate_final_credits(state: AnalysisState) -> float:
    """Calculates final credits with ALL multipliers."""
    ncrf_base = 0.0
    scan_metrics = state.get("scan_metrics")
    if scan_metrics and scan_metrics.get("ncrf"):
        ncrf_base = scan_metrics["ncrf"].get("ncrf_base_credits", 0.0)
    
    sfia_multiplier = 1.0
    sfia_result = state.get("sfia_result")
    if sfia_result:
        sfia_level = sfia_result.get("sfia_level", 3)
        multipliers = {1: 0.5, 2: 0.8, 3: 1.0, 4: 1.3, 5: 1.7}
        sfia_multiplier = multipliers.get(sfia_level, 1.0)
    
    reality_multiplier = 1.0
    audit_result = state.get("audit_result")
    if audit_result:
        reality_multiplier = audit_result.get("reality_multiplier", 1.0)
    
    quality_multiplier = 1.0
    if scan_metrics:
        quality_multiplier = scan_metrics.get("quality_multiplier", 1.0)
    
    # ✅ FIX: Read from ROOT state, not scan_metrics
    semantic_multiplier = state.get("semantic_multiplier", 1.0)
    
    final_credits = (
        ncrf_base 
        * sfia_multiplier 
        * reality_multiplier
        * quality_multiplier
        * semantic_multiplier
    )
    
    print(f"🧮 [Reporter] Credit Math: {ncrf_base:.2f} (Base) * {sfia_multiplier}x (SFIA) * {reality_multiplier}x (Reality) * {quality_multiplier}x (Qual) * {semantic_multiplier}x (Sem) = {final_credits:.2f}")
    
    return round(final_credits, 2)

async def _get_git_stability(state: AnalysisState) -> float:
    """
    Get git stability score from state (pre-calculated by Scanner).
    """
    scan_metrics = state.get("scan_metrics", {})
    git_stats = scan_metrics.get("git_stats", {})
    
    return git_stats.get("stability_score", 0.5)


def _generate_certificate(state: AnalysisState, validation_result: dict = None) -> dict:
    """
    Generates the certificate data structure.
    """
    repo_url = state.get("repo_url", "Unknown")
    validation = state.get("validation") or {}
    sfia_result = state.get("sfia_result") or {}
    final_credits = state.get("final_credits", 0.0)
    
    owner = validation.get("owner", "unknown")
    repo_name = validation.get("repo_name", "unknown")
    
    certificate = {
        "repo_url": repo_url,
        "repo_name": f"{owner}/{repo_name}",
        "credits_awarded": final_credits,
        "sfia_level": sfia_result.get("sfia_level"),
        "sfia_level_name": sfia_result.get("level_name"),
        "judge_ruling": sfia_result.get("judge_ruling"),
        "issued_at": datetime.utcnow().isoformat(),
        "verification_id": state.get("job_id"),
        "opik_trace_url": _build_opik_url(state.get("opik_trace_id"))
    }
    
    if validation_result:
        certificate["bayesian_validation"] = {
            "confidence": validation_result.get("confidence"),
            "bayesian_best": validation_result.get("bayesian_best_estimate"),
            "alert": validation_result.get("alert"),
            "reasoning": validation_result.get("reasoning")
        }
    
    return certificate


def _build_opik_url(trace_id: str) -> str:
    """Builds the URL to view the trace in the Comet/Opik dashboard"""
    if not trace_id:
        return None
    
    workspace = getattr(settings, 'OPIK_WORKSPACE', 'default')
    return f"https://www.comet.com/{workspace}/opik/traces/{trace_id}"


def _print_summary(state: AnalysisState, validation_result: dict = None):
    """Prints a CLI summary"""
    print(f"\n{'='*70}")
    print(f"📊 ANALYSIS SUMMARY: {state.get('job_id')}")
    print(f"{'='*70}\n")
    
    sfia_result = state.get("sfia_result", {})
    
    print(f"🏆 Final Level: {sfia_result.get('sfia_level')} ({sfia_result.get('level_name')})")
    print(f"💳 Credits: {state.get('final_credits', 0):.2f}")
    
    if validation_result:
        print(f"🔬 Bayesian Confidence: {validation_result.get('confidence', 0):.2%}")
        
    print(f"\n{'='*70}\n")