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
from app.services.scoring.engine import ScoringEngine
from app.services.scoring.quality_analyzer import CodeQualityAnalyzer

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


@track_agent(
    name="Scanner Agent",
    agent_type="tool",
    tags=["scanning", "multi-language", "tree-sitter", "quality-analysis", "agent"]
)
async def scan_codebase(state: AnalysisState) -> AnalysisState:
    """
    Agent 2: Scanner (ENHANCED WITH QUALITY ANALYSIS)
    
    Now includes:
    1. Tree-sitter multi-language analysis (existing)
    2. Code quality pattern detection (NEW)
    3. Semantic review (NEW)
    4. Git History Analysis (NEW)
    """
    
    state["current_step"] = "scanner"
    state["progress"] = get_progress_for_step("scanner")
    
    print(f"🔍 [Scanner Agent] Starting enhanced multi-language analysis...")
    
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="skillprotocol_")
        repo_path = Path(temp_dir) / "repo"
        
        print(f"📥 [Scanner Agent] Cloning repository...")
        
        # ====================================================================
        # 1. Clone repository
        # ====================================================================
        try:
            loop = asyncio.get_event_loop()
            
            clone_func = partial(
                git.Repo.clone_from,
                state["repo_url"],
                repo_path,
                depth=1,
                single_branch=True
            )
            
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
        
        # Verify clone
        if not repo_path.exists() or not any(repo_path.iterdir()):
            error_msg = "Repository clone succeeded but directory is empty"
            print(f"❌ [Scanner Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # 2. GIT HISTORY ANALYSIS (Project Maturity)
        # ====================================================================
        print(f"⏳ [Scanner Agent] Analyzing git history...")
        git_stats = {
            "commit_count": 1,
            "days_active": 0,
            "stability_score": 0.5, # Neutral default
            "is_new_repo": True
        }
        
        try:
            from app.services.validation.git_analyzer import get_git_analyzer
            
            # Use GitPython for raw counts (more robust here than external process)
            repo = git.Repo(repo_path)
            
            # Get stability from the Analyzer service
            git_analyzer = get_git_analyzer()
            stability_score = git_analyzer.analyze_stability(str(repo_path))
            
            # Simple fallback for dates if shallow clone
            commits = list(repo.iter_commits())
            commit_count = len(commits) # Will be low for shallow clone
            
            # If shallow clone (depth=1), commit count is 1. 
            # Ideally we'd use GitHub API for accurate counts, but we'll use what we have.
            if commit_count > 0:
                # Calculate active days (limited by clone depth)
                first_commit = commits[-1].committed_datetime
                last_commit = commits[0].committed_datetime
                days_active = (last_commit - first_commit).days
            else:
                days_active = 0
            
            git_stats = {
                "commit_count": commit_count,
                "days_active": days_active, 
                "stability_score": stability_score,
                "is_new_repo": commit_count < 3 # Heuristic for shallow/new repo
            }
            print(f"   📅 Days Active: {days_active}, Commits: {commit_count}")
            print(f"   Stability: {stability_score:.2f}")

        except Exception as e:
            print(f"⚠️ Git analysis warning: {e}")

        # ====================================================================
        # 3. Tree-sitter NCrF Analysis
        # ====================================================================
        engine = ScoringEngine()
        
        # Extract commit hash
        try:
            repo = git.Repo(repo_path)
            commit_hash = repo.head.object.hexsha
            print(f"📌 [Scanner Agent] Commit Hash: {commit_hash[:7]}")
        except Exception:
            commit_hash = "unknown"
        
        print(f"🔬 [Scanner Agent] Running Enhanced NCrF analysis with Tree-sitter...")
        
        try:
            ncrf_data = engine.calculate_ncrf_base_credits(str(repo_path))
            ncrf_data["repo_fingerprint"] = commit_hash 
            
            print(f"   - Files scanned: {ncrf_data['files_scanned']}")
            print(f"   - Total SLOC: {ncrf_data['total_sloc']}")
            print(f"   - Complexity: {ncrf_data['total_complexity']}")
            print(f"   - Maintainability Index: {ncrf_data['avg_mi']}")
            print(f"   - Base credits: {ncrf_data['ncrf_base_credits']}")
            
        except Exception as e:
            error_msg = f"NCrF calculation failed: {str(e)}"
            print(f"❌ [Scanner Agent] {error_msg}")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # 4. Detect SFIA Markers
        # ====================================================================
        print(f"🏷️  [Scanner Agent] Detecting SFIA markers (multi-language)...")
        
        try:
            sfia_markers = engine._detect_sfia_markers(str(repo_path))
            
            validation = state.get("validation")
            if validation and validation.get("markers"):
                api_markers = validation["markers"]
                for key in ["has_readme", "has_requirements", "has_ci_cd", "has_docker"]:
                    if key in api_markers:
                        sfia_markers[key] = api_markers[key]
            
            print(f"   - Has README: {sfia_markers.get('has_readme', False)}")
            print(f"   - Has Tests: {sfia_markers.get('has_tests', False)}")
            print(f"   - Has CI/CD: {sfia_markers.get('has_ci_cd', False)}")
            
        except Exception as e:
            error_msg = f"SFIA marker detection failed: {str(e)}"
            print(f"❌ [Scanner Agent] {error_msg}")
            state["errors"].append(error_msg)
            sfia_markers = {"has_readme": False}
        
        # ====================================================================
        # 5. QUALITY PATTERN ANALYSIS (Regex)
        # ====================================================================
        print(f"🎯 [Scanner Agent] Running code quality pattern analysis...")
        
        quality_multiplier = 1.0
        quality_report = {}
        
        try:
            # Get critical files to analyze
            sample_files = _get_critical_files(str(repo_path), n=10)
            
            if sample_files:
                quality_analyzer = CodeQualityAnalyzer()
                quality_report = quality_analyzer.analyze_repository(str(repo_path), sample_files)
                quality_multiplier = quality_report.get('average_quality_multiplier', 1.0)
                
                print(f"   ✅ Quality Multiplier: {quality_multiplier}x")
                print(f"   - Red Flags: {quality_report.get('red_flags_count', 0)}")
                print(f"   - Green Flags: {quality_report.get('green_flags_count', 0)}")
                print(f"   - Sophistication: {quality_report.get('sophistication', 'basic')}")
            else:
                print(f"   ⚠️  No suitable files for quality analysis")
                
        except Exception as e:
            print(f"⚠️  [Scanner Agent] Quality analysis failed: {str(e)}")
            # Continue without quality multiplier
        
        # ====================================================================
        # 6. SEMANTIC REVIEW (LLM - Enabled)
        # ====================================================================
        print(f"🧠 [Scanner Agent] Running Semantic Review...")
        semantic_multiplier = 1.0
        semantic_report = {}
        
        if sample_files and len(sample_files) > 0:
            try:
                from app.services.scoring.semantic_reviewer import SemanticCodeReviewer
                
                reviewer = SemanticCodeReviewer()
                semantic_report = await reviewer.review_repository_sample(
                    str(repo_path), 
                    sample_files[:3]  # Only review top 3 files for cost/speed
                )
                semantic_multiplier = semantic_report.get('semantic_multiplier', 1.0)
                
                print(f"   🧠 Semantic Multiplier: {semantic_multiplier}x")
                print(f"   - Insight: {semantic_report.get('key_insight')}")
                print(f"   - Score: {semantic_report.get('average_score')}/10")
                
            except Exception as e:
                print(f"⚠️  Semantic review failed: {str(e)}")
        
        # ====================================================================
        # 7. BUILD FINAL RESULT
        # ====================================================================
        raw_samples = sfia_markers.get("code_samples", [])
        code_samples = raw_samples[:2] if isinstance(raw_samples, list) else []
        
        markers_with_samples = {
            **{k: v for k, v in sfia_markers.items() if k != "code_samples"},
            "code_samples": code_samples
        }

        scan_result = {
            "ncrf": ncrf_data,
            "markers": markers_with_samples,
            "git_stats": git_stats,             # <--- History
            "quality_multiplier": quality_multiplier,
            "quality_report": quality_report,   # <--- Forensics
            "semantic_multiplier": semantic_multiplier,
            "semantic_report": semantic_report, # <--- Testimony
        }
        
        state["scan_metrics"] = scan_result
        
        print(f"✅ [Scanner Agent] Enhanced analysis complete")
        
        return state
        
    except Exception as e:
        error_msg = f"Scanner agent error: {str(e)}"
        print(f"❌ [Scanner Agent] {error_msg}")
        state["errors"].append(error_msg)
        return state
        
    finally:
        # Cleanup
        if temp_dir and Path(temp_dir).exists():
            try:
                # Use asyncio.to_thread for non-blocking cleanup
                await asyncio.to_thread(safe_cleanup, temp_dir)
                if not Path(temp_dir).exists():
                    print(f"🧹 [Scanner Agent] Cleaned up temporary files")
            except Exception as e:
                print(f"⚠️  [Scanner Agent] Failed to cleanup: {str(e)}")


# ============================================================================
# NEW HELPER FUNCTION
# ============================================================================

def _get_critical_files(repo_path: str, n: int = 10) -> list:
    """
    Sample the most important files for quality analysis
    (Don't analyze everything - too expensive)
    """
    
    candidates = []
    
    for root, _, files in os.walk(repo_path):
        # Skip common directories
        if any(skip in root for skip in ['node_modules', 'venv', '__pycache__', '.git', 'dist', 'build']):
            continue
        
        for file in files:
            # Only analyze code files
            ext = Path(file).suffix
            if ext not in ['.py', '.js', '.ts', '.tsx', '.java', '.go', '.rs', '.cpp']:
                continue
            
            file_path = os.path.join(root, file)
            
            try:
                # Score by size + depth (prefer larger, shallower files)
                size = Path(file_path).stat().st_size
                depth = len(Path(file_path).relative_to(repo_path).parts)
                
                # Core files are usually in root, larger, and not tests
                score = size * (1.0 / depth)
                
                # Boost score for main files
                if 'main' in file.lower() or 'app' in file.lower() or 'index' in file.lower():
                    score *= 2
                
                # Reduce score for test files
                if 'test' in file.lower() or 'spec' in file.lower():
                    score *= 0.3
                
                candidates.append((file_path, score))
                
            except Exception:
                continue
    
    # Return top N files
    sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    return [path for path, _ in sorted_candidates[:n]]