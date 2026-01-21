"""
Reporter Agent - SUPREME COURT COMPATIBLE
Respects Judge's verdicts and clears validation alerts if conflicts were resolved.
"""

from datetime import datetime
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent, log_to_main_project
from app.core.opik_advanced import OpikQualityDashboard

# NEW IMPORTS
from app.services.validation import get_validator, get_git_analyzer


@track_agent(
    name="Reporter Agent",
    agent_type="tool",
    tags=["final-scoring", "reporting", "agent"]
)
async def store_and_report(state: AnalysisState) -> AnalysisState:
    """
    Agent 5: Reporter (WITH BAYESIAN VALIDATION & JUDGE AWARENESS)
    
    Flow:
    1. Check validation success
    2. Calculate final credits
    3. Run Bayesian validation (if not already done)
    4. Sync with Judge's Verdict (Clear alerts if Judge resolved them)
    5. Save to database
    6. Generate certificate
    7. Log quality metrics
    8. Mark complete
    """
    
    # Update progress
    state["current_step"] = "reporter"
    state["progress"] = get_progress_for_step("reporter")
    
    print(f"📝 [Reporter Agent] Finalizing analysis...")
    
    try:
        # ====================================================================
        # STEP 1: Check if validation succeeded
        # ====================================================================
        validation = state.get("validation")
        
        if not validation or not validation.get("is_valid"):
            # Validation failed - create minimal report
            print(f"⚠️  [Reporter Agent] Validation failed, creating error report...")
            
            final_credits = 0.0
            state["final_credits"] = final_credits
            
            # Create error certificate
            certificate = {
                "repo_url": state.get("repo_url", "Unknown"),
                "credits_awarded": 0.0,
                "error": True,
                "error_reason": validation.get("error") if validation else "Validation failed",
                "error_type": validation.get("error_type") if validation else "UNKNOWN",
                "issued_at": datetime.utcnow().isoformat(),
                "verification_id": state.get("job_id")
            }
            
            state["certificate"] = certificate
            state["current_step"] = "complete"
            state["progress"] = 100
            state["completed_at"] = datetime.utcnow().isoformat()
            
            print(f"✅ [Reporter Agent] Error report complete")
            return state
        
        # ====================================================================
        # STEP 2: Calculate Final Credits (Normal Flow)
        # ====================================================================
        final_credits = _calculate_final_credits(state)
        state["final_credits"] = final_credits
        
        print(f"💳 [Reporter Agent] Final credits calculated: {final_credits:.2f}")
        
        # ====================================================================
        # STEP 2.5: BAYESIAN VALIDATION & JUDGE SYNC (CRITICAL UPDATE)
        # ====================================================================
        validation_result = state.get("validation_result")
        sfia_result = state.get("sfia_result", {})
        
        # 1. Check if Judge Intervened
        if sfia_result.get("judge_intervened"):
            print(f"⚖️ [Reporter Agent] Supreme Court ruled on this case.")
            
            # If the Judge resolved the conflict, we shouldn't show a scary "Alert"
            # We downgrade the alert to 'resolved' so the UI shows a checkmark, not a warning
            if validation_result:
                print("   ↳ Clearing statistical alert (Judge verdict takes precedence)")
                validation_result["alert"] = False
                validation_result["reasoning"] += " [RESOLVED BY JUDGE]"

        # 2. If validation is missing (shouldn't happen in new flow, but safe fallback)
        elif not validation_result and state.get("scan_metrics"):
            try:
                print(f"🔬 [Reporter Agent] Running late-bound Bayesian validation...")
                
                # Get git stability score
                git_stability = await _get_git_stability(state)
                
                # Run Bayesian validation
                validator = get_validator()
                validation_result = validator.validate_assessment(
                    predicted_level=state["sfia_result"].get("sfia_level", 3),
                    metrics=state["scan_metrics"],
                    git_stability=git_stability
                )
                
                # Log results
                confidence = validation_result["confidence"]
                alert = validation_result["alert"]
                bayesian_best = validation_result["bayesian_best_estimate"]
                predicted = state["sfia_result"].get("sfia_level")
                
                print(f"   Predicted Level: {predicted}")
                print(f"   Bayesian Best: {bayesian_best}")
                print(f"   Confidence: {confidence:.1%}")
                
                if alert:
                    print(f"⚠️  [Reporter Agent] VALIDATION ALERT!")
                    print(f"   {validation_result['reasoning']}")
                else:
                    print(f"✅ [Reporter Agent] Validation passed")
                
                # Store in state
                state["validation_result"] = validation_result
                
            except Exception as e:
                print(f"⚠️  [Reporter Agent] Bayesian validation failed: {str(e)}")
                validation_result = None
        
        # ====================================================================
        # STEP 3: Save to Database
        # ====================================================================
        print(f"💾 [Reporter Agent] Saving to database...")
        
        try:
            from app.models.database import save_analysis_result
            await save_analysis_result(state)
            print(f"✅ [Reporter Agent] Saved to database")
        except Exception as e:
            print(f"⚠️  [Reporter Agent] Database save failed: {str(e)}")
            state["errors"].append(f"Database save failed: {str(e)}")
            # Continue even if DB save fails
        
        # ====================================================================
        # STEP 4: Generate Certificate Data
        # ====================================================================
        certificate = _generate_certificate(state, validation_result)
        state["certificate"] = certificate

        # ====================================================================
        # STEP 5: LOG QUALITY METRICS TO OPIK (ENHANCED)
        # ====================================================================
        try:
            dashboard = OpikQualityDashboard()
            quality_metrics = dashboard.log_analysis_quality_metrics(
                state, 
                validation_result  # Pass validation results
            )
            
            print(f"✅ [Reporter Agent] Quality metrics logged to Opik:")
            print(f"   - SFIA Confidence: {quality_metrics.get('sfia_confidence', 0):.2%}")
            print(f"   - Duration: {quality_metrics.get('analysis_duration_seconds', 0):.1f}s")
            print(f"   - Reality Check: {'PASS' if quality_metrics.get('reality_check_passed') else 'FAIL'}")
            
            if validation_result:
                print(f"   - Bayesian Confidence: {quality_metrics.get('bayesian_confidence', 0):.2%}")
                if quality_metrics.get('bayesian_alert'):
                    print(f"   ⚠️  Validation Alert: {quality_metrics.get('validation_reasoning', '')}")
                    
        except Exception as e:
            print(f"⚠️  [Reporter Agent] Failed to log quality metrics: {str(e)}")
            # Don't fail the whole analysis if quality logging fails
        
        # ====================================================================
        # STEP 6: Mark as Complete
        # ====================================================================
        state["current_step"] = "complete"
        state["progress"] = 100
        state["completed_at"] = datetime.utcnow().isoformat()
        
        # ====================================================================
        # STEP 7: Print Summary
        # ====================================================================
        _print_summary(state, validation_result)
        
        print(f"✅ [Reporter Agent] Analysis complete!")
        
        # ====================================================================
        # STEP 8: Log final result to main project
        # ====================================================================
        try:
            log_to_main_project(
                name=f"Complete Analysis: {state.get('repo_url')}",
                input_data={
                    "repo_url": state.get("repo_url"),
                    "user_id": state.get("user_id")
                },
                output_data={
                    "final_credits": state.get("final_credits"),
                    "sfia_level": state.get("sfia_result", {}).get("sfia_level") if state.get("sfia_result") else 0,
                    "validation": state.get("validation"),
                    "scan_metrics": state.get("scan_metrics"),
                    "bayesian_validation": validation_result
                },
                metadata={
                    "job_id": state.get("job_id"),
                    "completed_at": state.get("completed_at"),
                    "bayesian_confidence": validation_result.get("confidence") if validation_result else None,
                    "validation_alert": validation_result.get("alert") if validation_result else None
                }
            )
        except Exception as e:
            print(f"⚠️  [Reporter Agent] Failed to log to main project: {str(e)}")
        
        return state
        
    except Exception as e:
        error_msg = f"Reporter agent error: {str(e)}"
        print(f"❌ [Reporter Agent] {error_msg}")
        state["errors"].append(error_msg)
        
        # Even on error, try to set some final credits
        state["final_credits"] = 0.0
        state["current_step"] = "complete"
        state["progress"] = 100
        state["completed_at"] = datetime.utcnow().isoformat()
        
        return state


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_final_credits(state: AnalysisState) -> float:
    """
    ENHANCED: Calculate final credits with ALL multipliers:
    - NCrF Base (size/complexity)
    - SFIA Level (skill level)
    - Reality Check (CI/CD tests pass)
    - Quality Patterns (NEW - code quality)
    - Semantic Review (NEW - LLM understanding)
    """
    
    # Get NCrF base credits
    ncrf_base = 0.0
    scan_metrics = state.get("scan_metrics")
    if scan_metrics and scan_metrics.get("ncrf"):
        ncrf_base = scan_metrics["ncrf"].get("ncrf_base_credits", 0.0)
    
    # Get SFIA multiplier
    sfia_multiplier = 1.0
    sfia_result = state.get("sfia_result")
    if sfia_result:
        sfia_level = sfia_result.get("sfia_level", 3)
        multipliers = {1: 0.5, 2: 0.8, 3: 1.0, 4: 1.3, 5: 1.7}
        sfia_multiplier = multipliers.get(sfia_level, 1.0)
    
    # Get reality check multiplier
    reality_multiplier = 1.0
    audit_result = state.get("audit_result")
    if audit_result:
        reality_multiplier = audit_result.get("reality_multiplier", 1.0)
    
    # NEW: Get quality multiplier
    quality_multiplier = 1.0
    if scan_metrics:
        quality_multiplier = scan_metrics.get("quality_multiplier", 1.0)
    
    # NEW: Get semantic multiplier (if enabled)
    semantic_multiplier = 1.0
    if scan_metrics:
        semantic_multiplier = scan_metrics.get("semantic_multiplier", 1.0)
    
    # Calculate final credits with ALL multipliers
    final_credits = (
        ncrf_base 
        * sfia_multiplier 
        * reality_multiplier
        * quality_multiplier    # <-- NEW
        * semantic_multiplier   # <-- NEW
    )
    
    print(f"🧮 [Reporter Agent] Enhanced Credit calculation:")
    print(f"   - NCrF Base: {ncrf_base:.2f}")
    print(f"   - SFIA Multiplier: {sfia_multiplier}x")
    print(f"   - Reality Multiplier: {reality_multiplier}x")
    print(f"   - Quality Multiplier: {quality_multiplier}x 🆕")
    
    if semantic_multiplier != 1.0:
        print(f"   - Semantic Multiplier: {semantic_multiplier}x 🆕")
    
    print(f"   - Final: {final_credits:.2f}")
    
    return round(final_credits, 2)

async def _get_git_stability(state: AnalysisState) -> float:
    """
    Get git stability score for validation
    
    Note: The repo has already been cloned and deleted by Scanner.
    We can't re-analyze git history, so we return a neutral value.
    
    Future enhancement: Scanner could store git metrics in state.
    """
    
    # TODO: Have Scanner Agent store git_stability in state
    # For now, return neutral value
    return 0.5


def _generate_certificate(state: AnalysisState, validation_result: dict = None) -> dict:
    """
    Generate certificate data with proper None checks
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
        "judge_ruling": sfia_result.get("judge_ruling"), # Include Judge's words
        "issued_at": datetime.utcnow().isoformat(),
        "verification_id": state.get("job_id"),
        "opik_trace_url": _build_opik_url(state.get("opik_trace_id"))
    }
    
    # Add Bayesian validation metadata
    if validation_result:
        certificate["bayesian_validation"] = {
            "confidence": validation_result.get("confidence"),
            "bayesian_best": validation_result.get("bayesian_best_estimate"),
            # Alert is cleared if Judge handled it
            "alert": validation_result.get("alert"),
            "reasoning": validation_result.get("reasoning")
        }
    
    return certificate


def _build_opik_url(trace_id: str) -> str:
    """Build Opik trace URL from trace ID"""
    
    if not trace_id:
        return None
    
    workspace = getattr(settings, 'OPIK_WORKSPACE', 'default')
    return f"https://www.comet.com/{workspace}/opik/traces/{trace_id}"


def _print_summary(state: AnalysisState, validation_result: dict = None):
    """Print a nice summary with None checks"""
    
    print(f"\n{'='*70}")
    print(f"📊 ANALYSIS SUMMARY")
    print(f"{'='*70}\n")
    
    # Repository info
    validation = state.get("validation")
    if validation:
        print(f"📦 Repository: {validation.get('owner')}/{validation.get('repo_name')}")
        print(f"   Language: {validation.get('language')}")
        print(f"   Size: {validation.get('size_kb')} KB\n")
    
    # Scan metrics
    scan_metrics = state.get("scan_metrics")
    if scan_metrics:
        ncrf = scan_metrics.get("ncrf", {})
        print(f"🔍 Code Analysis:")
        print(f"   Files scanned: {ncrf.get('files_scanned', 0)}")
        print(f"   Total SLOC: {ncrf.get('total_sloc', 0)}")
        print(f"   Complexity: {ncrf.get('total_complexity', 0)}")
        print(f"   Maintainability Index: {ncrf.get('avg_mi', 0)}")
        print(f"   Learning hours: {ncrf.get('estimated_learning_hours', 0)}")
        print(f"   Base credits: {ncrf.get('ncrf_base_credits', 0)}\n")
    
    # SFIA assessment
    sfia_result = state.get("sfia_result")
    if sfia_result:
        print(f"🏆 SFIA Assessment:")
        print(f"   Level: {sfia_result.get('sfia_level')} ({sfia_result.get('level_name')})")
        print(f"   LLM Confidence: {sfia_result.get('confidence', 0):.2%}")
        
        if sfia_result.get("judge_intervened"):
            print(f"   👨‍⚖️ Judge Verdict: {sfia_result.get('judge_ruling')}")
        else:
            print(f"   🤖 Grader Reasoning: {sfia_result.get('reasoning')[:100]}...")
        print()
        
        # Bayesian validation
        if validation_result:
            print(f"🔬 Bayesian Validation:")
            print(f"   Confidence: {validation_result.get('confidence', 0):.2%}")
            print(f"   Best Estimate: Level {validation_result.get('bayesian_best_estimate')}")
            
            if validation_result.get('alert'):
                print(f"   ⚠️  Alert: {validation_result.get('reasoning')}")
            else:
                print(f"   ✓ Status: Validated")
            print()
    
    # Reality check
    audit_result = state.get("audit_result")
    if audit_result:
        print(f"✓ Reality Check:")
        print(f"   Status: {'PASSED' if audit_result.get('reality_check_passed') else 'FAILED'}")
        print(f"   Penalty: {'Yes' if audit_result.get('penalty_applied') else 'No'}\n")
    
    # Final credits
    print(f"💳 FINAL CREDITS AWARDED: {state.get('final_credits', 0):.2f}")
    
    # Errors
    errors = state.get("errors", [])
    if errors:
        print(f"\n⚠️  Errors encountered: {len(errors)}")
        for error in errors[:3]:
            print(f"   - {error}")
    
    print(f"\n{'='*70}\n")