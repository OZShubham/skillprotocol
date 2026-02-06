import os
import stat
import sys
import asyncio
import tempfile
import shutil
import git
import json
import re
from pathlib import Path
from functools import partial, lru_cache
from typing import List, Dict, Any

from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.services.scoring.engine import ScoringEngine
from app.services.scoring.quality_analyzer import CodeQualityAnalyzer

# Opik and Live Streaming Imports
from opik import opik_context
from app.core.opik_config import track_agent
from app.utils.sse import push_live_log

# NEW: Import prompt manager
from app.core.prompt_manager import prompt_manager

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
# NEW: FILE READ CACHE (Performance Optimization)
# ============================================================================

@lru_cache(maxsize=200)
def _read_file_cached(file_path: str, max_chars: int = 5000) -> str:
    """Cache file reads to avoid duplicate I/O"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read(max_chars)
    except Exception:
        return ""

# ============================================================================
# NEW: SEMANTIC ANALYSIS (UPDATED FOR OPENROUTER)
# ============================================================================

async def _perform_semantic_analysis(
    sample_files: List[Dict[str, str]], 
    architecture_analysis: Dict[str, Any],
    quality_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform semantic analysis using OpenRouter (via PromptManager) to assess sophistication.
    """
    
    if not sample_files:
        return {
            "sophistication_score": 5,
            "semantic_multiplier": 1.0,
            "reasoning": "No code samples available",
            "analysis_skipped": True
        }
    
    # Prepare code samples
    code_samples_text = ""
    for idx, sample in enumerate(sample_files[:10], 1):
        code_samples_text += f"\n### Sample {idx}: {sample.get('path', 'unknown')}\n"
        code_samples_text += f"```\n{sample.get('content', '')[:3000]}\n```\n"
    
    # Build semantic analysis prompt
    semantic_prompt = f"""You are a Senior Software Architect performing semantic code analysis.

**Task:** Analyze the provided code samples and determine the architectural sophistication level.

**Automated Analysis Results:**
- Architecture Patterns Found: {architecture_analysis.get('unique_patterns_count', 0)}
- Sophistication Level: {architecture_analysis.get('sophistication_level', 'Unknown')}
- Quality Score: {quality_analysis.get('quality_score', 0)}
- Quality Level: {quality_analysis.get('quality_level', 'Unknown')}

**Code Samples:**
{code_samples_text}

**Detailed Findings:**
Design Patterns: {json.dumps(architecture_analysis.get('patterns_found', {}).get('design_patterns', []), indent=2)}
Architectural Styles: {json.dumps(architecture_analysis.get('patterns_found', {}).get('architectural_styles', []), indent=2)}
Sophistication Indicators: {json.dumps(architecture_analysis.get('patterns_found', {}).get('sophistication_indicators', []), indent=2)}

**Your Task:**
1. Validate the automated analysis findings
2. Identify any missed patterns or architectural insights
3. Assess the overall architectural maturity (1-10 scale)
4. Recommend semantic multiplier (0.5 to 1.5) where:
   - 0.5-0.8: Poor architecture, lacks patterns
   - 0.8-1.0: Basic architecture, some organization
   - 1.0-1.2: Good architecture, clear patterns
   - 1.2-1.5: Excellent architecture, advanced patterns

**Output Format (JSON ONLY):**
{{
    "architectural_maturity": <1-10>,
    "validated_patterns": ["list of confirmed patterns"],
    "additional_insights": "Any patterns or insights missed by automation",
    "semantic_multiplier": <0.5-1.5>,
    "reasoning": "Detailed explanation of your assessment",
    "confidence": <0.0-1.0>
}}

Output ONLY valid JSON, no markdown, no extra text.
"""
    
    try:
        # ---------------------------------------------------------
        # CHANGED: Use prompt_manager.call_llm (OpenAI SDK / OpenRouter)
        # ---------------------------------------------------------
        response_text = await prompt_manager.call_llm(
            prompt_text=semantic_prompt,
            model=settings.SEMANTIC_MODEL,  # Uses google/gemini-3-flash-preview
            temperature=0.1,
            json_mode=True,                 # Force JSON response format
            enable_reasoning=False          # Semantic analysis is fast, no deep reasoning needed
        )
        
        # Parse response
        # Sometimes models wrap JSON in markdown blocks even with json_mode
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        gemini_analysis = json.loads(clean_text)
    
    except Exception as e:
        print(f"⚠️ Semantic analysis failed: {e}")
        gemini_analysis = {
            "architectural_maturity": 5,
            "semantic_multiplier": 1.0,
            "reasoning": f"LLM analysis failed: {str(e)}. Using automated analysis.",
            "confidence": 0.6,
            "error": str(e)
        }
    
    # Validate multiplier
    final_multiplier = gemini_analysis.get("semantic_multiplier", 1.0)
    final_multiplier = max(0.5, min(1.5, final_multiplier))
    
    # Build complete report
    semantic_report = {
        "sophistication_score": architecture_analysis.get("sophistication_score", 5),
        "sophistication_level": architecture_analysis.get("sophistication_level", "Moderate"),
        "architectural_maturity": gemini_analysis.get("architectural_maturity", 5),
        "semantic_multiplier": final_multiplier,
        "architecture_analysis": {
            "patterns_found": architecture_analysis.get("patterns_found", {}),
            "unique_patterns_count": architecture_analysis.get("unique_patterns_count", 0),
            "files_analyzed": architecture_analysis.get("files_analyzed", 0)
        },
        "quality_analysis": quality_analysis,
        "gemini_insights": {
            "validated_patterns": gemini_analysis.get("validated_patterns", []),
            "additional_insights": gemini_analysis.get("additional_insights", ""),
            "confidence": gemini_analysis.get("confidence", 0.6)
        },
        "reasoning": gemini_analysis.get("reasoning", "Automated semantic analysis completed"),
        "multi_step_analysis": True,
        "analysis_complete": True
    }
    
    return semantic_report


def _analyze_architecture_patterns(sample_files: list, repo_path: str) -> dict:
    """
    Analyze code samples for architectural sophistication.
    MOVED FROM REVIEWER - No changes to logic
    """
    patterns_found = {
        "design_patterns": [],
        "architectural_styles": [],
        "code_organization": [],
        "sophistication_indicators": []
    }
    
    sophistication_score = 0
    files_analyzed = 0
    
    design_patterns = {
        "Factory": ["factory", "create_", "builder", "Factory"],
        "Singleton": ["singleton", "_instance", "getInstance"],
        "Strategy": ["Strategy", "interface", "implement"],
        "Observer": ["Observer", "subscribe", "notify", "listener"],
        "Decorator": ["decorator", "@", "wrapper"],
        "Adapter": ["Adapter", "adapt", "wrapper"],
        "Repository": ["Repository", "repo", "data access"],
        "Service": ["Service", "service layer", "business logic"],
        "Dependency Injection": ["inject", "container", "provide", "dependency"],
        "MVC": ["Model", "View", "Controller", "mvc"],
        "MVVM": ["ViewModel", "mvvm", "binding"],
        "Clean Architecture": ["usecase", "entity", "gateway", "presenter"],
        "Hexagonal": ["port", "adapter", "hexagonal"],
        "CQRS": ["Command", "Query", "cqrs"],
        "Event Sourcing": ["event", "sourcing", "aggregate"]
    }
    
    for sample in sample_files[:10]:
        content = sample.get("content", "")
        filepath = sample.get("path", "")
        files_analyzed += 1
        
        if not content:
            continue
        
        # Check for design patterns
        for pattern_name, keywords in design_patterns.items():
            if any(keyword in content for keyword in keywords):
                patterns_found["design_patterns"].append({
                    "pattern": pattern_name,
                    "file": filepath,
                    "evidence": f"Found {pattern_name} indicators"
                })
                sophistication_score += 2
        
        # Check for architectural organization
        if "class" in content and "def" in content:
            patterns_found["code_organization"].append({
                "indicator": "OOP Structure",
                "file": filepath
            })
            sophistication_score += 1
        
        # Check for separation of concerns
        if any(keyword in filepath.lower() for keyword in ["service", "controller", "model", "view", "repository", "dao"]):
            patterns_found["architectural_styles"].append({
                "style": "Layered Architecture",
                "evidence": f"Separated layer: {filepath}"
            })
            sophistication_score += 1
        
        # Async patterns
        if "async" in content and "await" in content:
            patterns_found["sophistication_indicators"].append({
                "indicator": "Asynchronous Programming",
                "file": filepath
            })
            sophistication_score += 2
        
        # Abstraction
        if "interface" in content or "abstract" in content or "ABC" in content:
            patterns_found["sophistication_indicators"].append({
                "indicator": "Abstraction/Interfaces",
                "file": filepath
            })
            sophistication_score += 2
        
        # Dependency injection
        if any(keyword in content for keyword in ["@inject", "container", "provide", "Injectable"]):
            patterns_found["sophistication_indicators"].append({
                "indicator": "Dependency Injection",
                "file": filepath
            })
            sophistication_score += 3
    
    # Calculate sophistication level
    if sophistication_score >= 20:
        sophistication_level = "Very High"
    elif sophistication_score >= 12:
        sophistication_level = "High"
    elif sophistication_score >= 6:
        sophistication_level = "Moderate"
    elif sophistication_score >= 2:
        sophistication_level = "Low"
    else:
        sophistication_level = "Minimal"
    
    return {
        "patterns_found": patterns_found,
        "sophistication_score": sophistication_score,
        "sophistication_level": sophistication_level,
        "files_analyzed": files_analyzed,
        "unique_patterns_count": len(patterns_found["design_patterns"]),
        "architectural_styles_count": len(patterns_found["architectural_styles"])
    }


def _analyze_code_quality(sample_files: list) -> dict:
    """
    Analyze code quality indicators from samples.
    MOVED FROM REVIEWER - No changes to logic
    """
    quality_indicators = {
        "documentation": 0,
        "error_handling": 0,
        "code_comments": 0,
        "type_safety": 0,
        "modularity": 0
    }
    
    for sample in sample_files[:10]:
        content = sample.get("content", "")
        
        if not content:
            continue
        
        # Check documentation
        if '"""' in content or "'''" in content or "/**" in content:
            quality_indicators["documentation"] += 1
        
        # Check error handling
        if any(keyword in content for keyword in ["try", "catch", "except", "throw", "raise"]):
            quality_indicators["error_handling"] += 1
        
        # Check comments
        comment_count = content.count("#") + content.count("//")
        if comment_count > 5:
            quality_indicators["code_comments"] += 1
        
        # Check type safety
        if any(keyword in content for keyword in [": str", ": int", ": bool", "typing", "type ", "interface"]):
            quality_indicators["type_safety"] += 1
        
        # Check modularity
        function_count = content.count("def ") + content.count("function ")
        if function_count > 3:
            quality_indicators["modularity"] += 1
    
    # Calculate quality score
    total_indicators = sum(quality_indicators.values())
    max_possible = len(sample_files[:10]) * 5
    quality_score = (total_indicators / max_possible) if max_possible > 0 else 0
    
    return {
        "quality_indicators": quality_indicators,
        "quality_score": round(quality_score, 3),
        "quality_level": "High" if quality_score >= 0.6 else "Moderate" if quality_score >= 0.3 else "Low"
    }


@track_agent(
    name="Scanner Agent (Enhanced)",
    agent_type="tool",
    tags=["scanning", "ncrf-layer", "semantic-analysis", "consolidated"]
)
async def scan_codebase(state: AnalysisState) -> AnalysisState:
    
    job_id = state["job_id"]
    state["current_step"] = "scanner"
    state["progress"] = get_progress_for_step("scanner")
    
    push_live_log(job_id, "scanner", "Initializing comprehensive analysis engine...", "success")
    
    temp_dir = None
    
    try:
        # Create sandbox
        temp_dir = tempfile.mkdtemp(prefix="skill_audit_")
        repo_path = Path(temp_dir) / "repo"
        
        push_live_log(job_id, "scanner", "Cloning repository...", "success")
        
        # ====================================================================
        # PHASE 1: CLONE
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
        except (asyncio.TimeoutError, git.exc.GitCommandError) as e:
            error_msg = f"Cloning failed: {str(e)}"
            push_live_log(job_id, "scanner", error_msg, "error")
            state["errors"].append(error_msg)
            state["should_skip"] = True
            return state

        # ====================================================================
        # PHASE 2: STATIC ANALYSIS - NCrF Layer
        # ====================================================================
        push_live_log(job_id, "scanner", "Running AST static analysis...", "success")
        engine = ScoringEngine()
        ncrf_data = engine.calculate_ncrf_base_credits(str(repo_path))
        
        # ====================================================================
        # PHASE 3: EXTRACT CODE SAMPLES 
        # ====================================================================
        push_live_log(job_id, "scanner", "Extracting code samples...", "success")
        critical_paths = _get_critical_files(str(repo_path), n=10)
        
        sample_files: List[Dict[str, str]] = []
        for p in critical_paths:
            try:
                rel_path = os.path.relpath(p, repo_path)
                content = _read_file_cached(p, 5000)  
                sample_files.append({
                    "path": rel_path,
                    "content": content
                })
            except Exception:
                continue
        
        # ====================================================================
        # PHASE 4: QUALITY ANALYSIS 
        # ====================================================================
        quality_analyzer = CodeQualityAnalyzer()
        quality_report = quality_analyzer.analyze_repository(
            str(repo_path),
            [str(Path(repo_path) / s['path']) for s in sample_files]
        )
        quality_multiplier = quality_report.get('average_quality_multiplier', 1.0)

        # ====================================================================
        # PHASE 5: GIT METRICS 
        # ====================================================================
        repo = git.Repo(repo_path)
        commits = list(repo.iter_commits())

        from app.services.validation.git_analyzer import get_git_analyzer
        git_analyzer = get_git_analyzer()
        stability_score = git_analyzer.analyze_stability(str(repo_path))
        
        git_stats = {
            "commit_count": len(commits),
            "is_one_shot": len(commits) < 3,
            "last_commit": commits[0].hexsha if commits else "none",
            "stability_score": stability_score
        }

        
        push_live_log(job_id, "scanner", "Analyzing architectural patterns...", "success")
        architecture_analysis = _analyze_architecture_patterns(sample_files, str(repo_path))
        
        
        push_live_log(job_id, "scanner", "Evaluating code quality indicators...", "success")
        quality_analysis = _analyze_code_quality(sample_files)
        
        
        # ====================================================================
        # PHASE 6: SEMANTIC ANALYSIS (UPDATED)
        # ====================================================================
        push_live_log(job_id, "scanner", "Performing semantic analysis with Gemini...", "success")
        semantic_report = await _perform_semantic_analysis(
            sample_files,
            architecture_analysis,
            quality_analysis
        )
        
        
        state["scan_metrics"] = {
            "ncrf": ncrf_data,
            "sample_files": sample_files,
            "git_stats": git_stats,
            "markers": engine._detect_sfia_markers(str(repo_path)),
            "quality_multiplier": quality_multiplier,
            "quality_report": quality_report,
            
            "architecture_analysis": architecture_analysis,
            "code_quality_analysis": quality_analysis,
            
            "semantic_report": semantic_report
        }
        
        state["semantic_multiplier"] = semantic_report["semantic_multiplier"]
        state["semantic_report"] = semantic_report
        
        # Log to Opik
        opik_context.update_current_trace(
            metadata={
                "total_sloc": ncrf_data.get("total_sloc"),
                "ncrf_base_credits": ncrf_data.get("ncrf_base_credits"),
                "semantic_multiplier": semantic_report["semantic_multiplier"],
                "sophistication_level": semantic_report["sophistication_level"]
            }
        )

        push_live_log(
            job_id, 
            "scanner", 
            f"Complete analysis finished. {ncrf_data['total_sloc']} SLOC, "
            f"Sophistication: {semantic_report['sophistication_level']}, "
            f"Semantic multiplier: {semantic_report['semantic_multiplier']}x",
            "success"
        )

        state["repo_path"] = str(repo_path)
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
# HELPER: GET CRITICAL FILES 
# ============================================================================

def _get_critical_files(repo_path: str, n: int = 10) -> list:
    """
    Heuristic to find 'Main Logic' files.
    """
    candidates = []
    logic_extensions = {'.py', '.js', '.ts', '.tsx', '.java', '.go', '.rs', '.cpp', '.cs'}
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
                depth = len(file_path.relative_to(repo_path).parts)
                
                score = size * (1.5 / depth)
                
                if any(k in file.lower() for k in ['main', 'app', 'core', 'service', 'controller', 'logic']):
                    score *= 2
                    
                candidates.append((str(file_path), score))
            except Exception:
                continue
                
    return [path for path, _ in sorted(candidates, key=lambda x: x[1], reverse=True)[:n]]