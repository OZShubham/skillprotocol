"""
Scanner Agent - PRODUCTION READY
Works on Windows, Linux, and Mac.
Fixes Opik logging and file permission errors.
Includes SSE Live Log streaming for real-time dashboard updates.
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

from app.services.scoring.engine import ScoringEngine
from app.services.scoring.quality_analyzer import CodeQualityAnalyzer

# Opik and Live Streaming Imports
from opik import opik_context
from app.core.opik_config import track_agent
from app.utils.sse import push_live_log # Integrated SSE function

# ============================================================================
# CROSS-PLATFORM CLEANUP HELPERS
# ============================================================================

def handle_remove_readonly(func, path, exc):
    """
    Error handler for shutil.rmtree to handle read-only file access errors.
    """
    excvalue = exc[1] if isinstance(exc, tuple) else exc 
    
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == 13: # EACCES
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    else:
        pass

def safe_cleanup(path: str):
    """
    Version-agnostic cleanup that handles Python 3.12+ deprecations.
    """
    if not path or not Path(path).exists():
        return

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
    Agent 2: Scanner (ENHANCED WITH QUALITY ANALYSIS & SSE STREAMING)
    """
    job_id = state["job_id"]
    state["current_step"] = "scanner"
    state["progress"] = get_progress_for_step("scanner")
    
    print(f"🔍 [Scanner Agent] Starting enhanced multi-language analysis...")
    push_live_log(job_id, "scanner", "Initializing multi-language analysis engine...", "success")
    
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="skillprotocol_")
        repo_path = Path(temp_dir) / "repo"
        
        print(f"📥 [Scanner Agent] Cloning repository...")
        push_live_log(job_id, "scanner", f"Cloning repository into temporary sandbox...", "success")
        
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
            push_live_log(job_id, "scanner", "Clone complete. Fingerprinting commit history...", "success")
            
        except asyncio.TimeoutError:
            error_msg = f"Repository clone timed out after {settings.CLONE_TIMEOUT_SECONDS} seconds"
            push_live_log(job_id, "scanner", error_msg, "error")
            state["errors"].append(error_msg)
            return state
            
        except git.exc.GitCommandError as e:
            error_msg = f"Git clone failed: {str(e)}"
            push_live_log(job_id, "scanner", "Access denied or repository not found.", "error")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # 2. GIT HISTORY ANALYSIS
        # ====================================================================
        push_live_log(job_id, "scanner", "Analyzing repository stability and developer cadence...", "success")
        git_stats = {"commit_count": 1, "days_active": 0, "stability_score": 0.5, "is_new_repo": True}
        
        try:
            from app.services.validation.git_analyzer import get_git_analyzer
            repo = git.Repo(repo_path)
            git_analyzer = get_git_analyzer()
            stability_score = git_analyzer.analyze_stability(str(repo_path))
            
            commits = list(repo.iter_commits())
            commit_count = len(commits)
            days_active = (commits[0].committed_datetime - commits[-1].committed_datetime).days if commit_count > 0 else 0
            
            git_stats = {
                "commit_count": commit_count,
                "days_active": days_active, 
                "stability_score": stability_score,
                "is_new_repo": commit_count < 3
            }
            push_live_log(job_id, "scanner", f"Git Analysis: {commit_count} commits across {days_active} active days.", "success")
        except Exception as e:
            print(f"⚠️ Git analysis warning: {e}")

        # ====================================================================
        # 3. Tree-sitter NCrF Analysis
        # ====================================================================
        engine = ScoringEngine()
        try:
            repo = git.Repo(repo_path)
            commit_hash = repo.head.object.hexsha
        except Exception:
            commit_hash = "unknown"
        
        push_live_log(job_id, "scanner", "Building Abstract Syntax Trees (AST) for multi-language parsing...", "success")
        
        try:
            ncrf_data = engine.calculate_ncrf_base_credits(str(repo_path))
            ncrf_data["repo_fingerprint"] = commit_hash 
            
            push_live_log(job_id, "scanner", f"Parsed {ncrf_data['total_sloc']} lines of code. Base NCrF: {ncrf_data['ncrf_base_credits']} credits.", "success")

            scores_to_log = [
                {"name": "metric_sloc", "value": float(ncrf_data['total_sloc']), "category_name": "static_analysis", "reason": "Total source lines"},
                {"name": "metric_complexity", "value": float(ncrf_data['total_complexity']), "category_name": "static_analysis", "reason": "Cyclomatic complexity"},
                {"name": "metric_maintainability", "value": float(ncrf_data['avg_mi']), "category_name": "static_analysis", "reason": "Maintainability index"}
            ]
            opik_context.update_current_span(feedback_scores=scores_to_log)
            opik_context.update_current_trace(feedback_scores=scores_to_log)
            
        except Exception as e:
            error_msg = f"NCrF calculation failed: {str(e)}"
            push_live_log(job_id, "scanner", "Structural analysis failed.", "error")
            state["errors"].append(error_msg)
            return state
        
        # ====================================================================
        # 4. Detect SFIA Markers
        # ====================================================================
        push_live_log(job_id, "scanner", "Detecting SFIA capability markers (CI/CD, Tests, Docker)...", "success")
        try:
            sfia_markers = engine._detect_sfia_markers(str(repo_path))
            validation = state.get("validation")
            if validation and validation.get("markers"):
                sfia_markers.update({k: v for k, v in validation["markers"].items() if k in ["has_readme", "has_requirements", "has_ci_cd", "has_docker"]})
        except Exception as e:
            print(f"❌ SFIA marker detection failed: {e}")
            sfia_markers = {"has_readme": False}
        
        # ====================================================================
        # 5. QUALITY PATTERN ANALYSIS
        # ====================================================================
        push_live_log(job_id, "scanner", "Scanning for anti-patterns and design sophistication...", "success")
        quality_multiplier = 1.0
        quality_report = {}
        
        try:
            sample_files = _get_critical_files(str(repo_path), n=10)
            if sample_files:
                quality_analyzer = CodeQualityAnalyzer()
                quality_report = quality_analyzer.analyze_repository(str(repo_path), sample_files)
                quality_multiplier = quality_report.get('average_quality_multiplier', 1.0)
                push_live_log(job_id, "scanner", f"Quality Check: {quality_report.get('sophistication')} level code detected.", "success")
        except Exception as e:
            print(f"⚠️ Quality analysis failed: {e}")
        
        # ====================================================================
        # 6. SEMANTIC REVIEW
        # ====================================================================
        push_live_log(job_id, "scanner", "Initiating LLM-based semantic code review...", "success")
        semantic_multiplier = 1.0
        semantic_report = {}
        
        if sample_files:
            try:
                from app.services.scoring.semantic_reviewer import SemanticCodeReviewer
                reviewer = SemanticCodeReviewer()
                semantic_report = await reviewer.review_repository_sample(str(repo_path), sample_files[:3])
                semantic_multiplier = semantic_report.get('semantic_multiplier', 1.0)
                push_live_log(job_id, "scanner", f"Semantic insight: {semantic_report.get('key_insight', 'Code reviewed.')[:50]}...", "success")
            except Exception as e:
                print(f"⚠️ Semantic review failed: {e}")
        
        # ====================================================================
        # 7. BUILD FINAL RESULT
        # ====================================================================
        raw_samples = sfia_markers.get("code_samples", [])
        state["scan_metrics"] = {
            "ncrf": ncrf_data,
            "markers": {**{k: v for k, v in sfia_markers.items() if k != "code_samples"}, "code_samples": raw_samples[:2]},
            "git_stats": git_stats,
            "quality_multiplier": quality_multiplier,
            "quality_report": quality_report,
            "semantic_multiplier": semantic_multiplier,
            "semantic_report": semantic_report,
        }
        
        push_live_log(job_id, "scanner", "Enhanced scanning complete. Handing off to Grader Agent.", "success")
        return state
        
    except Exception as e:
        error_msg = f"Scanner agent critical failure: {str(e)}"
        push_live_log(job_id, "scanner", "Critical scanning failure.", "error")
        state["errors"].append(error_msg)
        return state
        
    finally:
        if temp_dir and Path(temp_dir).exists():
            try:
                await asyncio.to_thread(safe_cleanup, temp_dir)
                print(f"🧹 [Scanner Agent] Sandbox cleaned")
            except Exception as e:
                print(f"⚠️ Sandbox cleanup failed: {e}")


def _get_critical_files(repo_path: str, n: int = 10) -> list:
    """
    Identifies core logic files by prioritizing size, depth, and keywords.
    """
    candidates = []
    for root, _, files in os.walk(repo_path):
        if any(skip in root for skip in ['node_modules', 'venv', '__pycache__', '.git', 'dist', 'build']):
            continue
        for file in files:
            ext = Path(file).suffix
            if ext not in ['.py', '.js', '.ts', '.tsx', '.java', '.go', '.rs', '.cpp']:
                continue
            file_path = os.path.join(root, file)
            try:
                stat_info = Path(file_path).stat()
                size = stat_info.st_size
                depth = len(Path(file_path).relative_to(repo_path).parts)
                score = size * (1.0 / depth)
                if any(k in file.lower() for k in ['main', 'app', 'index', 'core', 'service']):
                    score *= 2
                if any(k in file.lower() for k in ['test', 'spec', 'mock']):
                    score *= 0.3
                candidates.append((file_path, score))
            except Exception:
                continue
    return [path for path, _ in sorted(candidates, key=lambda x: x[1], reverse=True)[:n]]