"""
Reviewer Agent - FIXED FOR GEMINI 3 FLASH + OPIK PROMPT
Delivers forensic architectural deposition with strict evidence-backed analysis.
"""

import json
import logging
from typing import Dict, Any

from app.core.state import AnalysisState, get_progress_for_step
from app.core.opik_config import track_agent
from app.core.prompt_manager import prompt_manager
from app.utils.sse import push_live_log

logger = logging.getLogger(__name__)

@track_agent(name="Reviewer Agent", agent_type="llm", tags=["forensic-deposition", "gemini-3"])
async def review_semantics(state: AnalysisState) -> AnalysisState:
    """
    Agent 3: Forensic Architect (Expert Witness)
    
    Responsibilities:
    1. Analyze sample code files for architectural patterns
    2. Assess logic sophistication and engineering rigor
    3. Generate evidence-backed deposition for Judge Agent
    4. Apply semantic multiplier based on findings
    """
    
    job_id = state["job_id"]
    state["current_step"] = "reviewer"
    state["progress"] = get_progress_for_step("reviewer")
    
    # Get sample files from scanner
    samples = state.get("scan_metrics", {}).get("sample_files", [])
    
    if not samples:
        logger.warning(f"[Reviewer] No sample files for {job_id}, defaulting to neutral")
        push_live_log(job_id, "reviewer", "No code samples available, applying neutral assessment.", "warning")
        
        state["semantic_report"] = {
            "deposition_summary": "Insufficient evidence - No code samples provided.",
            "sophistication_score": 5,
            "semantic_multiplier": 1.0,
            "final_witness_statement": "Review skipped due to missing code samples."
        }
        state["semantic_multiplier"] = 1.0
        return state
    
    push_live_log(job_id, "reviewer", "Expert Witness: Commencing forensic architectural deposition...", "success")
    
    # Build the 'Codebase Under Oath' context
    file_context = ""
    for sample in samples[:10]:  # Limit to top 5 files
        file_context += f"\n{'='*60}\n"
        file_context += f"FILE: {sample['path']}\n"
        file_context += f"{'='*60}\n"
        file_context += sample['content'][:2500]  # Limit each file to 2500 chars
        file_context += "\n"
    
    try:
        # Fetch the forensic deposition prompt from Opik
        formatted_prompt = prompt_manager.format_prompt(
            "reviewer-agent-deposition",
            {"file_context": file_context}
        )
        
        push_live_log(job_id, "reviewer", "Analyzing architectural patterns and sophistication markers...", "success")
        
        # Execute via Gemini 3 Flash with LOW thinking (fast, structured analysis)
        raw_response = await prompt_manager.call_gemini(
            prompt_text=formatted_prompt,
            thinking_level="medium"  # Changed from "medium" for faster response
        )
        
        # Parse response
        report = json.loads(raw_response)
        
        # Validate required fields
        required_fields = ["deposition_summary", "sophistication_score", "semantic_multiplier", "final_witness_statement"]
        for field in required_fields:
            if field not in report:
                raise ValueError(f"Missing required field: {field}")
        
        # Normalize semantic multiplier (0.5 - 1.5 range)
        raw_multiplier = float(report.get("semantic_multiplier", 1.0))
        semantic_multiplier = max(0.5, min(1.5, raw_multiplier))
        
        # Normalize sophistication score (1-10 range)
        sophistication_score = max(1, min(10, int(report.get("sophistication_score", 5))))
        
        # Build exhibits summary for logging
        exhibits = report.get("exhibits", {})
        pattern_count = len(exhibits.get("architectural_patterns", []))
        sophistication_markers = len(exhibits.get("sophistication_markers", []))
        
        # Store detailed report in state
        state["semantic_report"] = {
            "deposition_summary": report["deposition_summary"],
            "exhibits": exhibits,
            "sophistication_score": sophistication_score,
            "semantic_multiplier": semantic_multiplier,
            "final_witness_statement": report["final_witness_statement"],
            "rigor_analysis": exhibits.get("rigor_analysis", "Not provided"),
            "sample_files_analyzed": len(samples)
        }
        
        state["semantic_multiplier"] = semantic_multiplier
        
        # Log success
        logger.info(f"[Reviewer] Job {job_id}: Score={sophistication_score}/10, Multiplier={semantic_multiplier}x")
        push_live_log(
            job_id, 
            "reviewer", 
            f"Deposition complete. Sophistication: {sophistication_score}/10. "
            f"Patterns detected: {pattern_count}. Multiplier: {semantic_multiplier}x",
            "success"
        )
        
        return state
        
    except json.JSONDecodeError as e:
        error_msg = f"Reviewer failed to parse Gemini response: {str(e)}"
        logger.error(f"[Reviewer] {error_msg}")
        push_live_log(job_id, "reviewer", "Deposition parsing failed. Applying neutral assessment.", "error")
        
        state["errors"].append(error_msg)
        state["semantic_report"] = {
            "deposition_summary": "Review failed - JSON parsing error",
            "sophistication_score": 5,
            "semantic_multiplier": 1.0,
            "final_witness_statement": "Technical error during review process."
        }
        state["semantic_multiplier"] = 1.0
        return state
        
    except Exception as e:
        error_msg = f"Reviewer critical failure: {str(e)}"
        logger.error(f"[Reviewer] {error_msg}")
        push_live_log(job_id, "reviewer", "Internal reviewer error. Defaulting to neutral.", "error")
        
        state["errors"].append(error_msg)
        state["semantic_report"] = {
            "deposition_summary": "Review failed - Internal error",
            "sophistication_score": 5,
            "semantic_multiplier": 1.0,
            "final_witness_statement": f"Error: {str(e)}"
        }
        state["semantic_multiplier"] = 1.0
        return state