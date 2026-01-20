"""
Scanner Agent - PRODUCTION READY
Works on Windows, Linux, and Mac.
Fixes Opik logging and file permission errors.
"""

import tempfile
import shutil
import git
import os
import stat
import sys
from pathlib import Path
import asyncio
from functools import partial
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent

# ============================================================================
# CROSS-PLATFORM CLEANUP HELPERS
# ============================================================================

def handle_remove_readonly(func, path, exc):
    """
    Error handler for shutil.rmtree.
    
    If the error is due to an access error (read only file, common with Git),
    it attempts to add write permission and then retries.
    """
    # Check if it's an access error (Windows code 5 or generic PermissionError)
    excvalue = exc[1] if isinstance(exc, tuple) else exc # Handle both old/new sigs
    
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == 13: # EACCES
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass # Best effort
    else:
        pass # Ignore other errors

def safe_cleanup(path: str):
    """
    Version-agnostic cleanup that handles Python 3.12+ deprecations
    """
    if not path or not Path(path).exists():
        return

    # Python 3.12+ uses 'onexc', older versions use 'onerror'
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=handle_remove_readonly)
    else:
        shutil.rmtree(path, onerror=handle_remove_readonly)

# ============================================================================
# SCANNER AGENT
# ============================================================================

@track_agent(
    name="Scanner Agent",
    agent_type="tool",
    tags=["scanning", "code-analysis", "agent"]
)
async def scan_codebase(state: AnalysisState) -> AnalysisState:
    """
    Agent 2: Scanner (HARDENED VERSION)
    
    Responsibilities:
    1. Clone the repository securely
    2. Analyze code structure and complexity (NCrF)
    3. Detect technical markers (SFIA)
    4. Clean up temporary files
    """
    
    # Update progress
    state["current_step"] = "scanner"
    state["progress"] = get_progress_for_step("scanner")
    
    print(f"🔍 [Scanner Agent] Starting code analysis...")
    
    temp_dir = None
    
    try:
        # ====================================================================
        # STEP 1: Create Temporary Directory
        # ====================================================================
        temp_dir = tempfile.mkdtemp(prefix="skillprotocol_")
        repo_path = Path(temp_dir) / "repo"
        
        print(f"📥 [Scanner Agent] Cloning repository to: {repo_path}")
        
        # ====================================================================
        # STEP 2: Clone Repository (With Manual Timeout)
        # ====================================================================
        try:
            # Use asyncio to add timeout to blocking git operation
            loop = asyncio.get_event_loop()
            
            # Wrap git.Repo.clone_from in a partial to pass to loop
            clone_func = partial(
                git.Repo.clone_from,
                state["repo_url"],
                repo_path,
                depth=1,  # Shallow clone
                single_branch=True  # Only default branch
            )
            
            # Run with asyncio timeout instead
            await asyncio.wait_for(
                loop.run_in_executor(None, clone_func),
                timeout=settings.CLONE_TIMEOUT_SECONDS
            )
            
            print(f"✅ [Scanner Agent] Clone complete")
            
        except asyncio.TimeoutError:
            error_msg = f"Repository clone timed out after {settings.CLONE_TIMEOUT_SECONDS} seconds"
            print(f"⏱️  [Scanner Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
            
        except git.exc.GitCommandError as e:
            error_msg = f"Git clone failed: {str(e)}"
            print(f"❌ [Scanner Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # STEP 3: Verify Clone Success
        # ====================================================================
        if not repo_path.exists() or not any(repo_path.iterdir()):
            error_msg = "Repository clone succeeded but directory is empty"
            print(f"❌ [Scanner Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # STEP 4: Import and Use Scoring Engine
        # ====================================================================
        try:
            from app.services.scoring.engine import ScoringEngine
        except ImportError as e:
            error_msg = f"Failed to import scoring_engine.py: {str(e)}"
            print(f"❌ [Scanner Agent] {error_msg}")
            print(f"💡 Make sure scoring_engine.py is at: app/services/scoring/engine.py")
            state["errors"].append(error_msg)
            return state
        
        engine = ScoringEngine()
        
        # --- ENHANCEMENT: EXTRACT COMMIT HASH FOR DEDUPLICATION ---
        try:
            repo = git.Repo(repo_path)
            commit_hash = repo.head.object.hexsha
            print(f"📌 [Scanner Agent] Commit Hash: {commit_hash[:7]}")
        except Exception:
            commit_hash = "unknown"
        
        print(f"🔬 [Scanner Agent] Running NCrF analysis...")
        
        # ====================================================================
        # STEP 5: Calculate NCrF Base Credits
        # ====================================================================
        try:
            ncrf_data = engine.calculate_ncrf_base_credits(str(repo_path))
            
            # INJECT THE COMMIT HASH INTO METRICS
            ncrf_data["repo_fingerprint"] = commit_hash 
            
            print(f"   - Files scanned: {ncrf_data['files_scanned']}")
            print(f"   - Total SLOC: {ncrf_data['total_sloc']}")
            print(f"   - Learning hours: {ncrf_data['estimated_learning_hours']}")
            print(f"   - Base credits: {ncrf_data['ncrf_base_credits']}")
            
        except Exception as e:
            error_msg = f"NCrF calculation failed: {str(e)}"
            print(f"❌ [Scanner Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # STEP 6: Detect SFIA Markers
        # ====================================================================
        print(f"🏷️  [Scanner Agent] Detecting SFIA markers...")
        
        try:
            sfia_markers = engine._detect_sfia_markers(str(repo_path))
            
            # Merge with markers detected by Validator (via API)
            validation = state.get("validation")
            if validation and validation.get("markers"):
                api_markers = validation["markers"]
                # API markers take precedence
                for key in ["has_readme", "has_requirements", "has_ci_cd", "has_docker"]:
                    if key in api_markers:
                        sfia_markers[key] = api_markers[key]
            
            print(f"   - Has README: {sfia_markers.get('has_readme', False)}")
            print(f"   - Has Tests: {sfia_markers.get('has_tests', False)}")
            print(f"   - Has CI/CD: {sfia_markers.get('has_ci_cd', False)}")
            print(f"   - Has Docker: {sfia_markers.get('has_docker', False)}")
            print(f"   - Uses OOP: {sfia_markers.get('uses_classes', False)}")
            print(f"   - Uses Async: {sfia_markers.get('uses_async', False)}")
            
        except Exception as e:
            error_msg = f"SFIA marker detection failed: {str(e)}"
            print(f"❌ [Scanner Agent] {error_msg}")
            state["errors"].append(error_msg)
            # Continue with empty markers
            sfia_markers = {
                "has_readme": False,
                "has_requirements": False,
                "has_tests": False,
                "has_ci_cd": False,
                "has_docker": False
            }
        
        # ====================================================================
        # STEP 7: Build Scan Result (with safe code samples)
        # ====================================================================
        # Extract code_samples safely
        raw_samples = sfia_markers.get("code_samples", [])
        code_samples = []
        
        if isinstance(raw_samples, list):
            code_samples = raw_samples[:2]  # Max 2 samples
        
        markers_with_samples = {
            **{k: v for k, v in sfia_markers.items() if k != "code_samples"},
            "code_samples": code_samples
        }

        scan_result = {
            "ncrf": ncrf_data,
            "markers": markers_with_samples,
        }
        
        state["scan_metrics"] = scan_result
        
        print(f"✅ [Scanner Agent] Analysis complete")
        
        return state
        
    except Exception as e:
        error_msg = f"Scanner agent error: {str(e)}"
        print(f"❌ [Scanner Agent] {error_msg}")
        state["errors"].append(error_msg)
        return state
        
    finally:
        # ====================================================================
        # CLEANUP: Always delete the cloned repository
        # ====================================================================
        if temp_dir and Path(temp_dir).exists():
            try:
                safe_cleanup(temp_dir)
                # Double check if it exists (sometimes it lingers on Windows)
                if not Path(temp_dir).exists():
                    print(f"🧹 [Scanner Agent] Cleaned up temporary files")
            except Exception as e:
                print(f"⚠️  [Scanner Agent] Failed to cleanup: {str(e)}")