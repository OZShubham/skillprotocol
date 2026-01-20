"""
Reporter Agent - FIXED VERSION
Handles missing validation/grader data gracefully
"""

from datetime import datetime
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent, log_to_main_project
from app.core.opik_advanced import OpikQualityDashboard

@track_agent(
    name="Reporter Agent",
    agent_type="tool",
    tags=["final-scoring", "reporting", "agent"]
)
async def store_and_report(state: AnalysisState) -> AnalysisState:
    """
    Agent 5: Reporter (HARDENED VERSION)
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
        certificate = _generate_certificate(state)
        state["certificate"] = certificate

        # ====================================================================
        # STEP 4.5: LOG QUALITY METRICS TO OPIK
        # ====================================================================
        try:
            dashboard = OpikQualityDashboard()
            quality_metrics = dashboard.log_analysis_quality_metrics(state)
            print(f"✅ [Reporter Agent] Quality metrics logged to Opik:")
            print(f"   - Confidence: {quality_metrics['sfia_confidence']:.2%}")
            print(f"   - Duration: {quality_metrics['analysis_duration_seconds']:.1f}s")
            print(f"   - Reality Check: {'PASS' if quality_metrics['reality_check_passed'] else 'FAIL'}")
        except Exception as e:
            print(f"⚠️  [Reporter Agent] Failed to log quality metrics: {str(e)}")
            # Don't fail the whole analysis if quality logging fails
        
        # ====================================================================
        # STEP 5: Mark as Complete
        # ====================================================================
        state["current_step"] = "complete"
        state["progress"] = 100
        state["completed_at"] = datetime.utcnow().isoformat()
        
        # ====================================================================
        # STEP 6: Print Summary
        # ====================================================================
        _print_summary(state)
        
        print(f"✅ [Reporter Agent] Analysis complete!")
        
        # Log final result to main project
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
                "scan_metrics": state.get("scan_metrics")
            },
            metadata={
                "job_id": state.get("job_id"),
                "completed_at": state.get("completed_at")
            }
        )
        
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


def _calculate_final_credits(state: AnalysisState) -> float:
    """
    Calculate final credits with proper None checks
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
        
        multipliers = {
            1: 0.5,   # Follow
            2: 0.8,   # Assist
            3: 1.0,   # Apply (baseline)
            4: 1.3,   # Enable
            5: 1.7    # Ensure
        }
        sfia_multiplier = multipliers.get(sfia_level, 1.0)
    
    # Get reality check multiplier
    reality_multiplier = 1.0
    audit_result = state.get("audit_result")
    if audit_result:
        reality_multiplier = audit_result.get("reality_multiplier", 1.0)
    
    # Calculate final credits
    final_credits = ncrf_base * sfia_multiplier * reality_multiplier
    
    print(f"🧮 [Reporter Agent] Credit calculation:")
    print(f"   - NCrF Base: {ncrf_base:.2f}")
    print(f"   - SFIA Multiplier: {sfia_multiplier}x")
    print(f"   - Reality Multiplier: {reality_multiplier}x")
    print(f"   - Final: {final_credits:.2f}")
    
    return round(final_credits, 2)


def _generate_certificate(state: AnalysisState) -> dict:
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
        "issued_at": datetime.utcnow().isoformat(),
        "verification_id": state.get("job_id"),
        "opik_trace_url": _build_opik_url(state.get("opik_trace_id"))
    }
    
    return certificate


def _build_opik_url(trace_id: str) -> str:
    """Build Opik trace URL from trace ID"""
    
    if not trace_id:
        return None
    
    workspace = getattr(settings, 'OPIK_WORKSPACE', 'default')
    return f"https://www.comet.com/{workspace}/opik/traces/{trace_id}"


def _print_summary(state: AnalysisState):
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
        print(f"   Learning hours: {ncrf.get('estimated_learning_hours', 0)}")
        print(f"   Base credits: {ncrf.get('ncrf_base_credits', 0)}\n")
    
    # SFIA assessment
    sfia_result = state.get("sfia_result")
    if sfia_result:
        print(f"🏆 SFIA Assessment:")
        print(f"   Level: {sfia_result.get('sfia_level')} ({sfia_result.get('level_name')})")
        print(f"   Confidence: {sfia_result.get('confidence', 0):.2%}")
        print(f"   Model: {sfia_result.get('model_used', 'unknown')}\n")
    
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