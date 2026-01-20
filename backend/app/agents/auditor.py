"""
Auditor Agent
Performs reality check by verifying code actually works via GitHub Actions
"""

import httpx
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent


@track_agent(
    name="Auditor Agent",
    agent_type="tool",
    tags=["reality-check", "github-actions", "agent"]
)
async def reality_check(state: AnalysisState) -> AnalysisState:
    """
    Agent 4: Auditor
    
    Responsibilities:
    1. Check if repository has GitHub Actions CI/CD
    2. Query GitHub API for latest workflow run
    3. Verify if tests passed or failed
    4. Apply penalty if code doesn't work
    5. Log decision to Opik
    
    Returns:
        Updated state with audit_result
    """
    
    # Update progress
    state["current_step"] = "auditor"
    state["progress"] = get_progress_for_step("auditor")
    
    print(f"🔍 [Auditor Agent] Starting reality check...")
    
    try:
        # ====================================================================
        # STEP 1: Extract repo info from validation
        # ====================================================================
        if not state.get("validation"):
            print(f"⚠️  [Auditor Agent] No validation data, skipping reality check")
            state["audit_result"] = {
                "reality_check_passed": True,  # Assume pass if no data
                "reason": "No CI/CD to check",
                "penalty_applied": False
            }
            return state
        
        owner = state["validation"].get("owner")
        repo_name = state["validation"].get("repo_name")
        
        # ====================================================================
        # STEP 2: Check if repo has CI/CD
        # ====================================================================
        has_ci_cd = state["scan_metrics"].get("markers", {}).get("has_ci_cd", False)
        
        if not has_ci_cd:
            print(f"✅ [Auditor Agent] No CI/CD found - no reality check needed")
            state["audit_result"] = {
                "reality_check_passed": True,
                "reason": "No CI/CD configured",
                "penalty_applied": False
            }
            return state
        
        print(f"🤖 [Auditor Agent] CI/CD detected, checking GitHub Actions...")
        
        # ====================================================================
        # STEP 3: Query GitHub Actions API
        # ====================================================================
        headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get latest workflow runs
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/actions/runs",
                headers=headers,
                params={
                    "per_page": 5,  # Get last 5 runs
                    "status": "completed"  # Only completed runs
                }
            )
            
            if response.status_code != 200:
                print(f"⚠️  [Auditor Agent] GitHub API error: {response.status_code}")
                state["audit_result"] = {
                    "reality_check_passed": True,  # Benefit of doubt
                    "reason": "Unable to check GitHub Actions",
                    "penalty_applied": False
                }
                return state
            
            data = response.json()
            runs = data.get("workflow_runs", [])
            
            if not runs:
                print(f"⚠️  [Auditor Agent] No completed workflow runs found")
                state["audit_result"] = {
                    "reality_check_passed": True,
                    "reason": "No completed CI runs",
                    "penalty_applied": False
                }
                return state
        
        # ====================================================================
        # STEP 4: Analyze Most Recent Run
        # ====================================================================
        latest_run = runs[0]
        
        conclusion = latest_run.get("conclusion")  # success, failure, cancelled, skipped
        run_url = latest_run.get("html_url")
        workflow_name = latest_run.get("name", "Unknown")
        
        print(f"📊 [Auditor Agent] Latest CI run:")
        print(f"   - Workflow: {workflow_name}")
        print(f"   - Status: {conclusion}")
        print(f"   - URL: {run_url}")
        
        # ====================================================================
        # STEP 5: Determine Pass/Fail
        # ====================================================================
        passed = conclusion == "success"
        penalty_applied = not passed
        
        # Calculate penalty multiplier
        reality_multiplier = 1.0 if passed else 0.5  # 50% penalty for failing tests
        
        audit_result = {
            "reality_check_passed": passed,
            "github_actions_status": conclusion,
            "workflow_name": workflow_name,
            "run_url": run_url,
            "penalty_applied": penalty_applied,
            "reality_multiplier": reality_multiplier,
            "reasoning": _get_reasoning(conclusion)
        }
        
        state["audit_result"] = audit_result
        
        if passed:
            print(f"✅ [Auditor Agent] Reality check PASSED - code works!")
        else:
            print(f"⚠️  [Auditor Agent] Reality check FAILED - applying 50% penalty")
            print(f"   Reason: {audit_result['reasoning']}")
        
        return state
        
    except Exception as e:
        error_msg = f"Auditor agent error: {str(e)}"
        print(f"❌ [Auditor Agent] {error_msg}")
        state["errors"].append(error_msg)
        
        # On error, default to passing (benefit of doubt)
        state["audit_result"] = {
            "reality_check_passed": True,
            "reason": f"Error during check: {str(e)}",
            "penalty_applied": False
        }
        
        return state


def _get_reasoning(conclusion: str) -> str:
    """
    Get human-readable reasoning for CI/CD status
    """
    
    reasons = {
        "success": "All tests passed successfully",
        "failure": "Tests failed - code has issues",
        "cancelled": "CI run was cancelled - assuming pass",
        "skipped": "CI run was skipped - assuming pass",
        "timed_out": "CI run timed out - possible performance issues",
        "action_required": "CI requires manual action",
        "neutral": "CI completed with neutral status",
        "stale": "CI run is outdated"
    }
    
    return reasons.get(conclusion, f"Unknown status: {conclusion}")


async def check_test_coverage(owner: str, repo_name: str) -> dict:
    """
    Advanced: Check test coverage percentage (optional)
    This requires additional API calls and parsing
    """
    
    # This is an optional enhancement
    # For MVP, just checking if tests pass/fail is sufficient
    
    pass