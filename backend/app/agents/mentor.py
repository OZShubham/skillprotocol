

import json
import logging
from typing import Dict, List, Any
from app.core.state import AnalysisState
from app.core.opik_config import track_agent
from app.core.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


@track_agent(
    name="Mentor Agent (Real Analysis)",
    agent_type="llm",
    tags=["mentor", "code-review", "markdown-report"]
)
async def provide_mentorship(state: AnalysisState) -> AnalysisState:
    
    
    job_id = state["job_id"]
    state["current_step"] = "mentor"
    
    logger.info(f"[Mentor] Starting real code analysis for {job_id}")
    
    try:
        # ====================================================================
        # STEP 1: Extract Rich Analysis Data from Scanner
        # ====================================================================
        scan_metrics = state.get("scan_metrics", {})
        sample_files = scan_metrics.get("sample_files", [])
        architecture = scan_metrics.get("architecture_analysis", {})
        quality = scan_metrics.get("code_quality_analysis", {})
        semantic = scan_metrics.get("semantic_report", {})
        ncrf = scan_metrics.get("ncrf", {})
        markers = scan_metrics.get("markers", {})
        
        sfia_result = state.get("sfia_result", {})
        current_level = sfia_result.get("sfia_level", 1)
        target_level = min(5, current_level + 1)
        
        # Skip if no code to analyze
        if not sample_files or ncrf.get("total_sloc", 0) == 0:
            logger.info(f"[Mentor] No code samples available, skipping mentorship")
            state["mentorship_plan"] = {
                "markdown_report": "# No Code Analysis Available\n\nInsufficient code samples for mentorship.",
                "current_level": current_level,
                "target_level": target_level,
                "missing_elements_count": 0,
                "issues_identified": 0
            }
            return state
        
        logger.info(f"[Mentor] Analyzing {len(sample_files)} code samples")
        
        # ====================================================================
        # STEP 2: Identify Specific Missing Elements
        # ====================================================================
        missing_elements = _identify_missing_elements(
            current_level=current_level,
            markers=markers,
            architecture=architecture,
            quality=quality
        )
        
        logger.info(f"[Mentor] Found {len(missing_elements)} missing elements")
        
        # ====================================================================
        # STEP 3: Analyze Code Quality Issues
        # ====================================================================
        code_issues = _extract_code_issues(
            sample_files=sample_files,
            quality=quality,
            architecture=architecture
        )
        
        logger.info(f"[Mentor] Identified {len(code_issues)} code issues")
        
        # ====================================================================
        # STEP 4: Build Comprehensive Context for Gemini
        # ====================================================================
        context = {
            "current_level": current_level,
            "target_level": target_level,
            "level_name": _get_level_name(current_level),
            "target_level_name": _get_level_name(target_level),
            
            # Code metrics
            "total_sloc": ncrf.get("total_sloc", 0),
            "file_count": ncrf.get("files_scanned", 0),
            "dominant_language": ncrf.get("dominant_language", "Unknown"),
            "complexity": ncrf.get("total_complexity", 0),
            
            # Analysis results
            "sophistication": semantic.get("sophistication_level", "Unknown"),
            "quality_level": quality.get("quality_level", "Unknown"),
            "patterns_found": architecture.get("unique_patterns_count", 0),
            "architecture_maturity": semantic.get("architectural_maturity", 5),
            
            # Specific findings
            "missing_elements": missing_elements,
            "code_issues": code_issues,
            
            # Code samples (first 3 files)
            "code_samples": _format_code_samples(sample_files[:3]),
            
            # Current strengths
            "strengths": _identify_strengths(markers, architecture, sfia_result)
        }
        
        # ====================================================================
        # STEP 5: Generate Detailed Markdown Report
        # ====================================================================
        logger.info(f"[Mentor] Generating personalized markdown report...")
        
        markdown_report = await _generate_mentorship_markdown(context)
        
        # ====================================================================
        # STEP 6: Save to State
        # ====================================================================
        state["mentorship_plan"] = {
            "markdown_report": markdown_report,
            "current_level": current_level,
            "target_level": target_level,
            "analysis_depth": "comprehensive",
            "code_samples_analyzed": len(sample_files[:3]),
            "missing_elements_count": len(missing_elements),
            "issues_identified": len(code_issues)
        }
        
        logger.info(f"[Mentor] Mentorship plan complete ({len(markdown_report)} chars)")
        
        return state
        
    except Exception as e:
        logger.error(f"[Mentor] Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback plan
        state["mentorship_plan"] = {
            "markdown_report": f"# Mentorship Unavailable\n\nError generating plan: {str(e)}",
            "current_level": state.get("sfia_result", {}).get("sfia_level", 1),
            "target_level": min(5, state.get("sfia_result", {}).get("sfia_level", 1) + 1),
            "error": str(e),
            "missing_elements_count": 0,
            "issues_identified": 0
        }
        
        return state


# ============================================================================
# ANALYSIS FUNCTIONS (Real, not fake tools)
# ============================================================================

def _identify_missing_elements(
    current_level: int,
    markers: Dict,
    architecture: Dict,
    quality: Dict
) -> List[Dict[str, Any]]:
    """
    Identify what's actually missing based on level requirements.
    Added 'concept' field to help the LLM explain the theory.
    """
    
    missing = []
    
    # Level 3 Requirements (Professional Baseline)
    if current_level < 3:
        if not markers.get("has_readme"):
            missing.append({
                "item": "README Documentation",
                "concept": "Technical Communication",
                "severity": "blocking",
                "level_required": 3,
                "why": "Level 3 requires clear project documentation",
                "how": "Create a README.md explaining what the project does, how to install, and usage examples"
            })
        
        if not markers.get("has_requirements"):
            missing.append({
                "item": "Dependency Management",
                "concept": "Reproducible Builds",
                "severity": "blocking",
                "level_required": 3,
                "why": "Professional projects must declare dependencies",
                "how": "Create requirements.txt, package.json, or equivalent for your language"
            })
        
        if not markers.get("has_modular_structure"):
            missing.append({
                "item": "Modular Code Organization",
                "concept": "Separation of Concerns",
                "severity": "blocking",
                "level_required": 3,
                "why": "Code must be organized into logical modules/files",
                "how": "Split code into separate files by responsibility (models, services, utils, etc.)"
            })
    
    # Level 4 Requirements (Enable)
    if current_level < 4:
        if not markers.get("has_tests"):
            missing.append({
                "item": "Unit Tests",
                "concept": "Test Driven Development (TDD)",
                "severity": "blocking",
                "level_required": 4,
                "why": "Level 4 requires test coverage to ensure code quality",
                "how": "Add unit tests using pytest, jest, or your language's testing framework. Aim for 60%+ coverage."
            })
        
        if not markers.get("has_error_handling"):
            missing.append({
                "item": "Error Handling",
                "concept": "Defensive Programming",
                "severity": "critical",
                "level_required": 4,
                "why": "Production code must handle failures gracefully",
                "how": "Add try-catch blocks, validate inputs, and provide meaningful error messages"
            })
        
        patterns_count = architecture.get("unique_patterns_count", 0)
        if patterns_count < 2:
            missing.append({
                "item": "Design Patterns",
                "concept": "Software Design Patterns",
                "severity": "important",
                "level_required": 4,
                "why": "Level 4 requires understanding of software design patterns",
                "how": "Implement patterns like Factory, Strategy, or Repository based on your use case"
            })
    
    # Level 5 Requirements (Ensure)
    if current_level < 5:
        if not markers.get("has_ci_cd"):
            missing.append({
                "item": "CI/CD Pipeline",
                "concept": "Continuous Integration",
                "severity": "blocking",
                "level_required": 5,
                "why": "Production systems require automated testing and deployment",
                "how": "Set up GitHub Actions, GitLab CI, or Jenkins to run tests on every commit"
            })
        
        if not markers.get("has_docker"):
            missing.append({
                "item": "Containerization",
                "concept": "Infrastructure as Code",
                "severity": "important",
                "level_required": 5,
                "why": "Level 5 requires deployment-ready infrastructure",
                "how": "Create a Dockerfile and docker-compose.yml for consistent environments"
            })
        
        if not markers.get("uses_async"):
            missing.append({
                "item": "Asynchronous Programming",
                "concept": "Concurrency Models",
                "severity": "important",
                "level_required": 5,
                "why": "Scalable systems use async patterns for efficiency",
                "how": "Implement async/await for I/O operations, API calls, and database queries"
            })
    
    return missing


def _extract_code_issues(
    sample_files: List[Dict],
    quality: Dict,
    architecture: Dict
) -> List[Dict[str, Any]]:
    """
    Extract specific code quality issues from analysis.
    Returns concrete problems with their files.
    """
    
    issues = []
    
    # Quality indicators
    quality_indicators = quality.get("quality_indicators", {})
    
    if quality_indicators.get("documentation", 0) == 0:
        issues.append({
            "type": "Missing Docstrings",
            "severity": "medium",
            "description": "Functions lack documentation strings",
            "impact": "Makes code harder to understand and maintain",
            "fix": "Add docstrings to all functions explaining purpose, parameters, and return values"
        })
    
    if quality_indicators.get("error_handling", 0) < len(sample_files) * 0.5:
        issues.append({
            "type": "Insufficient Error Handling",
            "severity": "high",
            "description": "Less than 50% of files have error handling",
            "impact": "Code will crash on unexpected inputs",
            "fix": "Add try-except blocks for operations that can fail (file I/O, API calls, parsing)"
        })
    
    if quality_indicators.get("type_safety", 0) < len(sample_files) * 0.3:
        issues.append({
            "type": "Missing Type Hints",
            "severity": "low",
            "description": "Type annotations are sparse",
            "impact": "Reduces IDE support and makes bugs harder to catch",
            "fix": "Add type hints to function signatures: def process(data: dict) -> list:"
        })
    
    # Architecture issues
    patterns_found = architecture.get("patterns_found", {})
    if not patterns_found.get("design_patterns"):
        issues.append({
            "type": "No Design Patterns",
            "severity": "medium",
            "description": "Code lacks structured design patterns",
            "impact": "Harder to extend and maintain as project grows",
            "fix": "Consider implementing Factory, Strategy, or Repository patterns where appropriate"
        })
    
    return issues


def _identify_strengths(
    markers: Dict,
    architecture: Dict,
    sfia_result: Dict
) -> List[str]:
    """
    Identify what the developer is already doing well.
    """
    
    strengths = []
    
    if markers.get("has_readme"):
        strengths.append("Clear documentation with README")
    
    if markers.get("has_tests"):
        strengths.append("Test coverage present")
    
    if markers.get("has_ci_cd"):
        strengths.append("Automated CI/CD pipeline configured")
    
    if markers.get("has_docker"):
        strengths.append("Containerization with Docker")
    
    if markers.get("uses_async"):
        strengths.append("Uses asynchronous programming patterns")
    
    patterns_count = architecture.get("unique_patterns_count", 0)
    if patterns_count > 0:
        strengths.append(f"Implements {patterns_count} design patterns")
    
    sophistication = architecture.get("sophistication_level", "Low")
    if sophistication in ["High", "Very High"]:
        strengths.append(f"High code sophistication ({sophistication})")
    
    confidence = sfia_result.get("confidence", 0)
    if confidence >= 0.8:
        strengths.append(f"Clear skill demonstration ({confidence:.0%} confidence)")
    
    return strengths if strengths else ["Functional codebase"]


def _format_code_samples(sample_files: List[Dict]) -> str:
    """
    Format code samples for inclusion in the prompt.
    """
    
    if not sample_files:
        return "No code samples available."
    
    formatted = ""
    
    for idx, sample in enumerate(sample_files[:3], 1):
        path = sample.get("path", "unknown")
        content = sample.get("content", "")[:800]  # Limit to 800 chars
        
        formatted += f"\n### Sample {idx}: {path}\n```\n{content}\n```\n"
    
    return formatted


# ============================================================================
# MARKDOWN GENERATION - 
# ============================================================================

async def _generate_mentorship_markdown(context: Dict) -> str:
    """
    Generate detailed, personalized markdown report using Gemini.
    """
    
    # 1. Update Prompt to request specific JSON Schema
    # This aligns with the 'ProviderStrategy' pattern since PromptManager forces JSON.
    prompt = f"""You are a Senior Software Development Mentor providing personalized career guidance.

**Developer Profile:**
- Current SFIA Level: {context['current_level']} ({context['level_name']})
- Target Level: {context['target_level']} ({context['target_level_name']})
- Language: {context['dominant_language']}
- Project Size: {context['file_count']} files, {context['total_sloc']} lines
- Sophistication: {context['sophistication']}
- Quality Level: {context['quality_level']}
- Patterns Found: {context['patterns_found']}
- Architecture Maturity: {context['architecture_maturity']}/10

**Current Strengths:**
{chr(10).join(f"- {s}" for s in context['strengths'])}

**Missing for Next Level ({len(context['missing_elements'])} items):**
{chr(10).join(f"- Missing Item: {m['item']} (Concept: {m.get('concept', 'General')}) - {m['why']}" for m in context['missing_elements'])}

**Code Quality Issues ({len(context['code_issues'])} found):**
{chr(10).join(f"- {i['type']} ({i['severity']}) - {i['description']}" for i in context['code_issues'])}

**Code Samples from Their Repository:**
{context['code_samples']}

**Your Task:**
Create a detailed, personalized mentorship report in Markdown format.

**CORE REQUIREMENT - THE "LEARN THEN APPLY" APPROACH:**
Since specific concepts (like "{context['missing_elements'][0]['concept'] if context['missing_elements'] else 'Best Practices'}") are missing, you must assume the user might not fully understand the *theory* behind them yet.
Do not just tell them to "Write a test". First, explain *what* TDD is and *why* it matters for their specific level.

**Markdown Structure:**

1. **👋 Current Assessment**: Warm greeting, acknowledging their current level and specific strengths found in the code.

2. **📚 Concept Gap Analysis (THEORY)**:
   - Look at the "Missing for Next Level" list.
   - For the top 2-3 missing concepts, explain the *theory* simply.
   - Example: If 'CI/CD' is missing, explain "What is Continuous Integration?" and why a Level {context['target_level']} developer needs it.
   - Recommend 1-2 specific topics to read/study (e.g., "Read about GitHub Actions Workflow syntax").

3. **🛠️ Priority Improvements (PRACTICE)**:
   - Identify 3-5 priority improvements ranked by impact.
   - Connect these directly to the concepts explained above.
   - Provide concrete code examples matching their language ({context['dominant_language']}).

4. **⚡ Quick Wins**: 2-3 things they can do TODAY (e.g., add type hints, fix a specific anti-pattern).

5. **📈 Your Roadmap**: A week-by-week plan to learn the concepts and then implement them.

6. **💰 Credit Projection**: Show how these changes increase their verified skill credits.

**CRITICAL OUTPUT INSTRUCTION:**
You MUST respond with a valid JSON object containing exactly one key: "mentorship_report".
The value must be the full Markdown string.

Example Output Format:
{{
    "mentorship_report": "# Your Path... (full markdown here)"
}}
"""

    try:
        # 2. Call Gemini (It is already configured to return JSON in prompt_manager)
        response_json_str = await prompt_manager.call_gemini(
            prompt_text=prompt,
            thinking_level="medium",
            temperature=0.7
        )
        
        # 3. Parse the Structured Output
        try:
            data = json.loads(response_json_str)
            
            # Extract the specific field defined in our schema
            markdown_content = data.get("mentorship_report")
            
            if not markdown_content:
                # Fallback if key is missing but 'markdown' or 'report' exists
                markdown_content = data.get("markdown") or data.get("report") or response_json_str
                
            # If it's still a dict/object (nested), stringify it or take a best guess
            if isinstance(markdown_content, dict):
                 markdown_content = json.dumps(markdown_content)

            return markdown_content.strip()
            
        except json.JSONDecodeError:
            # Fallback if model failed to produce valid JSON (rare with Gemini 2.0/3.0)
            logger.warning("[Mentor] Failed to parse JSON, returning raw response")
            # Attempt to strip code fences if present
            clean_resp = response_json_str.strip()
            if clean_resp.startswith("```json"):
                clean_resp = clean_resp[7:]
            if clean_resp.endswith("```"):
                clean_resp = clean_resp[:-3]
            return clean_resp.strip()
        
    except Exception as e:
        logger.error(f"[Mentor] Generation failed: {e}")
        return f"# Error\nCould not generate report: {str(e)}"


def _get_level_name(level: int) -> str:
    """Get SFIA level name."""
    names = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
    return names.get(level, "Unknown")