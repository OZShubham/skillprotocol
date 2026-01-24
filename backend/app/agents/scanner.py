"""
Scanner Agent - PRODUCTION READY
Optimized for multi-agent handoff, capturing structural code samples for Semantic Review.
"""

import os
import stat
import sys
import asyncio
import tempfile
import shutil
import git
from pathlib import Path
from functools import partial
from typing import List, Dict, Any

from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.services.scoring.engine import ScoringEngine
from app.services.scoring.quality_analyzer import CodeQualityAnalyzer

# Opik and Live Streaming Imports
from opik import opik_context
from app.core.opik_config import track_agent
from app.utils.sse import push_live_log

# ============================================================================
# CROSS-PLATFORM CLEANUP HELPERS
# ============================================================================

def handle_remove_readonly(func, path, exc):
    """Handles read-only file access errors during cleanup (common on Windows/Git)."""
    excvalue = exc[1] if isinstance(exc, tuple) else exc 
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == 13:
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

def safe_cleanup(path: str):
    """Version-agnostic directory cleanup."""
    if not path or not Path(path).exists():
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=handle_remove_readonly)
    else:
        shutil.rmtree(path, onerror=handle_remove_readonly)

# ============================================================================
# SCANNER AGENT NODE
# ============================================================================

@track_agent(
    name="Scanner Agent",
    agent_type="tool",
    tags=["scanning", "ncrf-layer", "source-extraction"]
)
async def scan_codebase(state: AnalysisState) -> AnalysisState:
    """
    Agent 2: Scanner
    1. Clones the repository.
    2. Runs NCrF static analysis (SLOC/Complexity).
    3. Extracts actual code content from critical files for the Reviewer Agent.
    """
    job_id = state["job_id"]
    state["current_step"] = "scanner"
    state["progress"] = get_progress_for_step("scanner")
    
    push_live_log(job_id, "scanner", "Initializing forensic extraction engine...", "success")
    
    temp_dir = None
    
    try:
        # Create sandbox
        temp_dir = tempfile.mkdtemp(prefix="skill_audit_")
        repo_path = Path(temp_dir) / "repo"
        
        push_live_log(job_id, "scanner", "Cloning repository into temporary sandbox...", "success")
        
        # 1. CLONE REPOSITORY
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
        except (asyncio.TimeoutError, git.exc.GitCommandError) as e:
            error_msg = f"Cloning failed: {str(e)}"
            push_live_log(job_id, "scanner", error_msg, "error")
            state["errors"].append(error_msg)
            state["should_skip"] = True
            return state

        # 2. STATIC ANALYSIS (NCrF Layer)
        push_live_log(job_id, "scanner", "Running AST static analysis (Tree-sitter)...", "success")
        engine = ScoringEngine()
        ncrf_data = engine.calculate_ncrf_base_credits(str(repo_path))
        
        # 3. CRITICAL FILE EXTRACTION (The Bridge to Reviewer Agent)
        push_live_log(job_id, "scanner", "Extracting high-value code samples for architectural review...", "success")
        critical_paths = _get_critical_files(str(repo_path), n=10)
        
        sample_files: List[Dict[str, str]] = []
        for p in critical_paths:
            try:
                # Calculate relative path for the report
                rel_path = os.path.relpath(p, repo_path)
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    # Capture up to 5000 chars (enough for deep context, safe for LLM windows)
                    content = f.read(5000)
                    sample_files.append({
                        "path": rel_path,
                        "content": content
                    })
            except Exception:
                continue
        
        # ✅ ADD THIS: Calculate Quality Multiplier
        quality_analyzer = CodeQualityAnalyzer()
        quality_report = quality_analyzer.analyze_repository(
            str(repo_path),
            [str(Path(repo_path) / s['path']) for s in sample_files]
        )
        
        quality_multiplier = quality_report.get('average_quality_multiplier', 1.0)

        # 4. GIT METRICS
        repo = git.Repo(repo_path)
        commits = list(repo.iter_commits())

        from app.services.validation.git_analyzer import get_git_analyzer
        git_analyzer = get_git_analyzer()
        stability_score = git_analyzer.analyze_stability(str(repo_path))
        
        git_stats = {
            "commit_count": len(commits),
            "is_one_shot": len(commits) < 3,
            "last_commit": commits[0].hexsha if commits else "none",
            "stability_score": stability_score  # ✅ STORE IT NOW
        }

        # 5. CONSOLIDATE SCAN METRICS
        # Note: 'sample_files' is used by the Reviewer Agent, 'ncrf' by the Judge
        state["scan_metrics"] = {
        "ncrf": ncrf_data,
        "sample_files": sample_files,
        "git_stats": git_stats,
        "markers": engine._detect_sfia_markers(str(repo_path)),
        "quality_multiplier": quality_multiplier,  # ✅ NOW INCLUDED
        "quality_report": quality_report  # ✅ Full details for Judge
         }
        # Log metrics to Opik for traceability
        opik_context.update_current_trace(
            metadata={
                "total_sloc": ncrf_data.get("total_sloc"),
                "ncrf_base_credits": ncrf_data.get("ncrf_base_credits"),
                "detected_language": ncrf_data.get("dominant_language")
            }
        )

        push_live_log(job_id, "scanner", f"Analysis complete. Found {ncrf_data['total_sloc']} SLOC across {len(sample_files)} logic modules.", "success")
        return state

    except Exception as e:
        error_msg = f"Scanner critical failure: {str(e)}"
        push_live_log(job_id, "scanner", error_msg, "error")
        state["errors"].append(error_msg)
        return state
        
    finally:
        if temp_dir:
            await asyncio.to_thread(safe_cleanup, temp_dir)

# ============================================================================
# UTILS
# ============================================================================

def _get_critical_files(repo_path: str, n: int = 10) -> list:
    """
    Heuristic to find 'Main Logic' files. 
    Prioritizes file size, directory depth, and architectural keywords.
    """
    candidates = []
    # Extensions that typically contain core business logic
    logic_extensions = {'.py', '.js', '.ts', '.tsx', '.java', '.go', '.rs', '.cpp', '.cs'}
    # Ignore noise
    ignored_dirs = {'node_modules', 'venv', '__pycache__', '.git', 'dist', 'build', 'tests', 'docs'}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d.lower() not in ignored_dirs]
        
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix not in logic_extensions:
                continue
                
            try:
                stat_info = file_path.stat()
                size = stat_info.st_size
                # Depth: shallow files are often more "core" (main.py, index.ts)
                depth = len(file_path.relative_to(repo_path).parts)
                
                # Scoring algorithm
                score = size * (1.5 / depth)
                
                # Boost if name sounds like entry point or core logic
                if any(k in file.lower() for k in ['main', 'app', 'core', 'service', 'controller', 'logic']):
                    score *= 2
                    
                candidates.append((str(file_path), score))
            except Exception:
                continue
                
    # Sort by score descending and return top N paths
    return [path for path, _ in sorted(candidates, key=lambda x: x[1], reverse=True)[:n]]