

import json
import logging
import re
from typing import Dict, Any, List, Literal, Union
from pathlib import Path

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.tools import tool
from pydantic import BaseModel, Field

from app.core.state import AnalysisState
from app.core.config import settings
from app.core.opik_config import track_agent
from app.utils.sse import push_live_log

logger = logging.getLogger(__name__)



LEVEL_CRITERIA = {
    "1": {
        "name": "Beginner - Follow",
        "sloc": {"min": 0, "max": 500},
        "required": {"testing": "None", "cicd": "No", "patterns": 0, "docs": "None"},
        "indicators": ["Single file", "No structure", "Tutorial code"]
    },
    "2": {
        "name": "Intermediate - Assist",
        "sloc": {"min": 500, "max": 2000},
        "required": {"testing": "Optional", "cicd": "No", "patterns": 0, "docs": "Basic README"},
        "indicators": ["Some structure", "Config files", "Basic organization"]
    },
    "3": {
        "name": "Competent - Apply",
        "sloc": {"min": 2000, "max": 8000},
        "required": {"testing": "Unit tests", "cicd": "Optional", "patterns": 1, "docs": "README + docs"},
        "must_have_3_of": ["Tests", "Patterns", "Logging", "Config", "Docs", "Error handling"],
        "indicators": ["Clear structure", "Tests present", "Some patterns"]
    },
    "4": {
        "name": "Advanced - Enable",
        "sloc": {"min": 8000, "max": 30000},
        "required": {"testing": "Unit + Integration", "cicd": "REQUIRED", "patterns": 3, "docs": "Comprehensive"},
        "must_have_5_of": ["CI/CD", "Tests", "3+ Patterns", "Docker", "Logging", "Config", "Docs", "Error handling"],
        "disqualifiers": ["No CI/CD → Level 3", "No tests → Level 3"],
        "indicators": ["CI/CD present", "Multiple patterns", "Production-ready"]
    },
    "5": {
        "name": "Expert - Ensure",
        "sloc": {"min": 30000, "max": 1000000},
        "required": {"testing": "All levels (80%+)", "cicd": "Multi-stage + IaC", "patterns": 5, "docs": "Enterprise-grade"},
        "must_have_8_of": ["Microservices", "K8s", "All tests", "IaC", "Monitoring", "Advanced CI/CD", "5+ Patterns", "Event-driven", "Security", "Performance"],
        "disqualifiers": ["No K8s/orchestration → Level 4", "SLOC < 20K → unlikely Level 5"],
        "indicators": ["Microservices", "K8s", "Enterprise scale", "Production proven"]
    }
}

# ============================================================================
# TOOL 1: GET LEVEL CRITERIA 
# ============================================================================

@tool
def get_level_criteria(level: int) -> str:
    """Get detailed criteria for specific SFIA level."""
    level_str = str(level)
    if level_str not in LEVEL_CRITERIA:
        return json.dumps({"error": f"Invalid level {level}. Must be 1-5."})
    
    return json.dumps({
        "level": level,
        **LEVEL_CRITERIA[level_str]
    })

# ============================================================================
# TOOL 2: VALIDATE LEVEL ASSIGNMENT 
# ============================================================================

@tool
def validate_level_assignment(
    proposed_level: int,
    has_tests: bool,
    has_cicd: bool,
    pattern_count: int,
    sloc: int,
    has_comprehensive_docs: bool,
    has_docker: bool = False,
    has_monitoring: bool = False
) -> str:
    """
    Validate if repository meets criteria for proposed level.
    Returns pass/fail for each requirement + final recommendation.
    """
    
    level_str = str(proposed_level)
    if level_str not in LEVEL_CRITERIA:
        return json.dumps({"error": "Invalid level"})
    
    criteria = LEVEL_CRITERIA[level_str]
    checks = {}
    passes = 0
    fails = 0
    
    # SLOC check
    sloc_min = criteria["sloc"]["min"]
    sloc_max = criteria["sloc"]["max"]
    sloc_pass = sloc_min <= sloc <= sloc_max
    checks["sloc"] = {
        "required": f"{sloc_min}-{sloc_max}",
        "actual": sloc,
        "pass": sloc_pass
    }
    if sloc_pass:
        passes += 1
    else:
        fails += 1
    
    # Testing check
    if proposed_level >= 3:
        checks["testing"] = {
            "required": criteria["required"]["testing"],
            "actual": "Present" if has_tests else "Missing",
            "pass": has_tests
        }
        if has_tests:
            passes += 1
        else:
            fails += 1
    
    # CI/CD check (CRITICAL for Level 4+)
    if proposed_level >= 4:
        checks["cicd"] = {
            "required": "CI/CD pipeline",
            "actual": "Present" if has_cicd else "Missing",
            "pass": has_cicd,
            "critical": True
        }
        if has_cicd:
            passes += 1
        else:
            fails += 1
    
    # Pattern check
    required_patterns = criteria["required"]["patterns"]
    if proposed_level >= 3:
        patterns_pass = pattern_count >= required_patterns
        checks["patterns"] = {
            "required": f"{required_patterns}+ patterns",
            "actual": f"{pattern_count} patterns",
            "pass": patterns_pass
        }
        if patterns_pass:
            passes += 1
        else:
            fails += 1
    
    # Documentation check
    if proposed_level >= 3:
        checks["documentation"] = {
            "required": criteria["required"]["docs"],
            "actual": "Present" if has_comprehensive_docs else "Basic",
            "pass": has_comprehensive_docs
        }
        if has_comprehensive_docs:
            passes += 1
        else:
            fails += 1
    
    # Calculate pass rate
    total_checks = len(checks)
    pass_rate = passes / total_checks if total_checks > 0 else 0
    
    # Determine recommendation
    if pass_rate >= 0.8:
        recommendation = f"✅ APPROVED for Level {proposed_level}"
    elif pass_rate >= 0.6:
        recommendation = f"⚠️ BORDERLINE for Level {proposed_level} - review evidence carefully"
    else:
        recommendation = f"❌ REJECTED for Level {proposed_level} - consider Level {max(1, proposed_level - 1)}"
    
    # Apply disqualifiers
    if proposed_level >= 4 and not has_cicd:
        recommendation = "❌ DISQUALIFIED from Level 4+ (no CI/CD) - Maximum Level 3"
    
    if proposed_level >= 3 and not has_tests:
        recommendation = "❌ DISQUALIFIED from Level 3+ (no tests) - Maximum Level 2"
    
    return json.dumps({
        "proposed_level": proposed_level,
        "level_name": criteria["name"],
        "checks": checks,
        "passes": passes,
        "fails": fails,
        "pass_rate": round(pass_rate, 2),
        "recommendation": recommendation
    })

# ============================================================================
# TOOL 3: READ SELECTED FILES 
# ============================================================================

@tool
def read_selected_files(repo_path: str, file_paths: List[str], max_lines: int = 300) -> str:
    """
    Read specific files for spot-checking claims.
    Use SPARINGLY - most analysis already done by Scanner.
    
    Args:
        repo_path: Path to repository
        file_paths: List of relative file paths
        max_lines: Max lines per file
    
    Returns:
        JSON with file contents
    """
    
    if not repo_path or not isinstance(repo_path, str):
        return json.dumps({"error": "Invalid repo_path"})
    
    if not isinstance(file_paths, list) or not file_paths:
        return json.dumps({"error": "No file paths provided"})
    
    try:
        root_path = Path(repo_path).resolve()
    except Exception as e:
        return json.dumps({"error": f"Cannot parse path: {str(e)}"})
    
    if not root_path.exists() or not root_path.is_dir():
        return json.dumps({"error": "Repository path not found"})
    
    results = []
    max_files = 5  # Limit to prevent abuse
    
    for file_path in file_paths[:max_files]:
        try:
            # Security check
            if ".." in file_path or file_path.startswith("/"):
                results.append({
                    "path": file_path,
                    "error": "Invalid path (security)",
                    "error_type": "SECURITY_VIOLATION"
                })
                continue
            
            full_path = root_path / file_path
            
            # Verify within repo
            if not str(full_path.resolve()).startswith(str(root_path)):
                results.append({
                    "path": file_path,
                    "error": "Path outside repository",
                    "error_type": "SECURITY_VIOLATION"
                })
                continue
            
            # Check existence
            if not full_path.exists():
                results.append({
                    "path": file_path,
                    "error": "File not found",
                    "error_type": "NOT_FOUND"
                })
                continue
            
            # Check size
            file_size = full_path.stat().st_size
            if file_size > 500_000:
                results.append({
                    "path": file_path,
                    "error": f"File too large: {file_size} bytes",
                    "error_type": "FILE_TOO_LARGE"
                })
                continue
            
            # Read file
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                total_lines = len(lines)
                content = ''.join(lines[:max_lines])
            
            results.append({
                "success": True,
                "path": file_path,
                "content": content,
                "total_lines": total_lines,
                "truncated": total_lines > max_lines
            })
            
        except Exception as e:
            results.append({
                "path": file_path,
                "error": str(e),
                "error_type": "READ_ERROR"
            })
    
    if not results:
        return json.dumps({"error": "No files could be read"})
    
    return json.dumps(results)

# ============================================================================
# STRUCTURED OUTPUT SCHEMA 
# ============================================================================

class GraderResult(BaseModel):
    """Final assessment result from the grader"""
    sfia_level: int = Field(description="SFIA level 1-5", ge=1, le=5)
    confidence: float = Field(description="Confidence 0.0-1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Clear explanation of the assessment")
    evidence: List[str] = Field(description="Key evidence supporting the decision")
    rubric_validation: Dict[str, Any] = Field(description="Validation results against rubric")
    patterns_found: int = Field(description="Number of design patterns identified")
    bayesian_agreement: bool = Field(description="Whether assessment aligns with Bayesian prior")

# ============================================================================
# MAIN GRADER FUNCTION
# ============================================================================

@track_agent(
    name="Grader Agent (Refactored)",
    agent_type="llm",
    tags=["modern", "simplified-tools", "uses-scanner-data", "efficient"]
)
async def grade_sfia_level(state: AnalysisState) -> AnalysisState:
    """
    Grader Agent - REFACTORED
    
    Key Changes:
    - Uses pre-analyzed data from Scanner (no redundant analysis)
    - Simplified from 7 tools to 3 tools
    - Faster execution (fewer tool calls)
    - Same accuracy (all data still available)
    """
    
    job_id = state["job_id"]
    state["current_step"] = "grader"
    
    logger.info(f"[🎓 Grader] Starting (Refactored) for {job_id}")
    push_live_log(job_id, "grader", "🚀 Grader: Using pre-analyzed data from Scanner...", "success")
    
    # ====================================================================
    # EXTRACT PRE-ANALYZED DATA FROM SCANNER
    # ====================================================================
    scan_metrics = state.get("scan_metrics", {})
    if not scan_metrics:
        state["errors"].append("No scan metrics")
        return state
    
    # NCrF data
    ncrf = scan_metrics.get("ncrf", {})
    
    # Markers
    markers = scan_metrics.get("markers", {})
    
    # Architecture analysis (NEW from Scanner)
    architecture = scan_metrics.get("architecture_analysis", {})
    patterns_found = architecture.get("unique_patterns_count", 0)
    sophistication = architecture.get("sophistication_level", "Unknown")
    
    # Quality analysis (NEW from Scanner)
    quality = scan_metrics.get("code_quality_analysis", {})
    quality_level = quality.get("quality_level", "Unknown")
    
    # Semantic analysis (NEW from Scanner)
    semantic = scan_metrics.get("semantic_report", {})
    architectural_maturity = semantic.get("architectural_maturity", 5)
    
    # Bayesian prior
    validation_result = state.get("validation_result", {})
    bayesian_level = validation_result.get("bayesian_best_estimate", 3)
    bayesian_confidence = validation_result.get("confidence", 0.5)
    
    repo_path = state.get("repo_path", "")
    
    # Initialize LLM
    llm = ChatGroq(
        model=settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.1,
        max_retries=2
    )
    
    # Define simplified tools
    tools = [
        get_level_criteria,
        validate_level_assignment,
        read_selected_files  # Only for spot-checks if needed
    ]
    
    # ====================================================================
    # ENHANCED SYSTEM PROMPT - Uses Pre-Analyzed Data
    # ====================================================================
    system_prompt = f"""You are an Elite SFIA Assessment Specialist.

**🎯 MISSION:** Accurately assess SFIA level (1-5) using pre-analyzed data.

**📊 PRE-ANALYZED REPOSITORY DATA (from Scanner):**

**Quantitative Metrics:**
- SLOC: {ncrf.get('total_sloc', 0):,}
- Complexity: {ncrf.get('total_complexity', 0)}
- Complexity Density: {ncrf.get('complexity_density', 0):.3f}
- Maintainability Index: {ncrf.get('avg_mi', 65)}/100
- Language: {ncrf.get('dominant_language', 'Unknown')}
- Files Analyzed: {ncrf.get('files_scanned', 0)}

**Architectural Analysis:**
- Design Patterns Found: {patterns_found}
- Sophistication Level: {sophistication}
- Architectural Maturity: {architectural_maturity}/10
- Quality Level: {quality_level}

**Detected Markers:**
- ✓ README: {markers.get('has_readme', False)}
- ✓ Tests: {markers.get('has_tests', False)}
- ✓ CI/CD: {markers.get('has_ci_cd', False)}
- ✓ Docker: {markers.get('has_docker', False)}
- ✓ Error Handling: {markers.get('has_error_handling', False)}
- ✓ Async Patterns: {markers.get('uses_async', False)}
- ✓ Modular Structure: {markers.get('has_modular_structure', False)}

**🔮 STATISTICAL ANCHOR (Bayesian Prior):**
- Bayesian Model Estimate: Level {bayesian_level} ({bayesian_confidence:.0%} confidence)
- This is your STARTING POINT - deviate only with strong evidence

**🛠️ AVAILABLE TOOLS (Use Strategically):**

1. `get_level_criteria(level)` - Get rubric for a specific level
2. `validate_level_assignment(...)` - Validate if repo meets level criteria
3. `read_selected_files(...)` - Spot-check specific files (USE SPARINGLY)

**⚠️ CRITICAL: You already have comprehensive analysis above.**
**Do NOT use read_selected_files unless absolutely necessary to verify a specific claim.**

**🧠 ASSESSMENT WORKFLOW:**

**Step 1: Form Initial Hypothesis**
Based on the pre-analyzed data above, what level seems appropriate?
Consider:
- SLOC range
- Pattern count
- Markers present
- Bayesian prior

**Step 2: Get Rubric Criteria**
Use `get_level_criteria(your_hypothesis)` to see exact requirements

**Step 3: Validate Against Rubric**
Use `validate_level_assignment(...)` with the data provided above

**Step 4: Make Final Decision**
Based on validation results:
- If pass_rate >= 80%: Approve level
- If pass_rate < 60%: Try level below
- Check for disqualifiers (no CI/CD → max L3, no tests → max L2)

**Step 5: Only if Uncertain**
If validation is borderline AND you need to verify specific code:
- Use `read_selected_files` to spot-check 1-2 critical files
- This should be RARE - trust the Scanner's analysis

**⚠️ CRITICAL RULES:**
1. TRUST the pre-analyzed data - it's comprehensive
2. Use tools to GET RUBRIC and VALIDATE, not re-analyze
3. Cite specific evidence from the metrics above
4. Respect disqualifiers
5. Align with Bayesian prior unless you have strong contrary evidence

Repository Path (for spot-checks only): {repo_path}

Provide your final assessment in the structured GraderResult format.
"""
    
    try:
        # Create agent with simplified tools
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            response_format=ToolStrategy(
                schema=GraderResult,
                handle_errors=True
            )
        )
        
        # Run agent
        push_live_log(job_id, "grader", "🔍 Evaluating against SFIA rubric...", "success")
        
        result = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"Assess SFIA level for this repository using the pre-analyzed data provided."
            }]
        })
        
        # Extract structured response
        grader_result = result.get("structured_response")
        
        if not grader_result:
            raise ValueError("No structured response from agent")
        
        push_live_log(job_id, "grader", "✅ Assessment complete!", "success")
        
        # Convert to dict if Pydantic model
        if isinstance(grader_result, BaseModel):
            grader_result = grader_result.model_dump()
        
        # Add metadata
        tool_calls_made = len([
            msg for msg in result.get("messages", [])
            if hasattr(msg, "tool_calls") and msg.tool_calls
        ])
        
        grader_result["tool_calls_made"] = tool_calls_made
        grader_result["_grader_refactored"] = True
        grader_result["used_scanner_analysis"] = True
        grader_result["statistical_prior"] = bayesian_level
        
        state["sfia_result"] = grader_result
        
        logger.info(
            f"[✅ Grader] Level {grader_result['sfia_level']} "
            f"({grader_result['confidence']:.0%} confidence) "
            f"using {tool_calls_made} tool calls (vs ~8 previously)"
        )
        
        return state
        
    except Exception as e:
        logger.error(f"[❌ Grader] Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback
        state["sfia_result"] = {
            "sfia_level": bayesian_level,
            "confidence": bayesian_confidence,
            "reasoning": f"Grader failed: {str(e)[:100]}. Using Bayesian estimate.",
            "evidence": [],
            "rubric_validation": {},
            "patterns_found": patterns_found,
            "bayesian_agreement": True,
            "tool_calls_made": 0,
            "_fallback": True
        }
        
        return state