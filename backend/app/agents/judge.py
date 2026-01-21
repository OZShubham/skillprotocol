"""
Judge Agent (Supreme Court - Deliberative Version)
Intervenes in EVERY analysis to synthesize LLM intuition, Statistical priors, and Hard Evidence.
Uses Chain-of-Thought reasoning to reach a nuanced verdict.
"""

import json
from openai import AsyncOpenAI
from opik import track

from app.core.config import settings
from app.core.state import AnalysisState, get_progress_for_step

@track(name="Judge Agent", type="llm", tags=["judge", "supreme-court", "deliberation"])
async def arbitrate_level(state: AnalysisState) -> AnalysisState:
    """
    Agent 4.5: The Supreme Judge
    
    Responsibilities:
    1. Review the entire case file (Grader output + Bayesian Prior + Hard Metrics).
    2. Deliberate on conflicts using Chain of Thought.
    3. Issue a final, binding verdict with detailed justification.
    """
    
    state["current_step"] = "judge"
    state["progress"] = get_progress_for_step("judge")
    
    # 1. Gather Evidence
    sfia_result = state.get("sfia_result")
    validation_result = state.get("validation_result")
    ncrf = state.get("scan_metrics", {}).get("ncrf", {})
    markers = state.get("scan_metrics", {}).get("markers", {})
    
    # Fail-safe: If critical data is missing, we cannot judge properly
    if not sfia_result or not validation_result:
        print("⚖️ [Judge Agent] Missing assessment data. Skipping review.")
        return state

    llm_level = int(sfia_result.get("sfia_level", 0))
    stats_level = int(validation_result.get("bayesian_best_estimate", 0))
    stats_conf = validation_result.get("confidence", 0.0)

    print(f"👨‍⚖️ [Judge Agent] Deliberating Case. Grader: {llm_level} | Stats: {stats_level} ({stats_conf:.1%})")

    # 2. Construct the "Deliberation" Case File
    # We provide all evidence and ask the model to argue the case before deciding.
    case_file_prompt = f"""
You are the Supreme Technical Arbiter for the SkillProtocol Certification Board.
Your goal is truth and accuracy. You must resolve discrepancies between an AI Assessor and a Statistical Model.

**CASE # {state.get('job_id', 'UNKNOWN')}**

**The Conflict:**
* **Assessor A (Grader Agent):** Recommends **Level {llm_level}** ({sfia_result.get('level_name')})
  * *Argument:* "{sfia_result.get('reasoning')}"
  * *Confidence:* {sfia_result.get('confidence', 0):.1%}

* **Assessor B (Statistical Model):** Suggests **Level {stats_level}**
  * *Reasoning:* "{validation_result.get('reasoning')}"
  * *Confidence:* {stats_conf:.1%}
  * *Plausible Range:* {validation_result.get('expected_range')}

**The Hard Evidence (Forensics):**
1. **Scale:** {ncrf.get('total_sloc')} lines of code.
2. **Quality:** Maintainability Index is {ncrf.get('avg_mi')}/100.
3. **Complexity:** Total Cyclomatic Complexity is {ncrf.get('total_complexity')}.
4. **Key Technical Markers:**
   - CI/CD Pipelines: {markers.get('has_ci_cd')}
   - Containerization (Docker): {markers.get('has_docker')}
   - Async/Concurrent Patterns: {markers.get('uses_async')}
   - Unit Tests: {markers.get('has_tests')}
   - Design Patterns (OOP/Interfaces): {markers.get('uses_design_patterns')}

**Deliberation Instructions:**
You must think step-by-step to resolve this.
1. **Analyze the Discrepancy:** Why did the Grader give a different score than the Stats? Was the Grader hallucinating quality that isn't there? Or is the Statistical model too conservative for this specific architecture?
2. **Evaluate the 'Production' Standard:** Level 4+ generally requires automation (CI/CD) and containerization. Does this repo have it? If not, is there a valid reason (e.g., it's a library, not a service)?
3. **Weigh Complexity vs. Size:** A small repo (Level 3 size) can be Level 5 complexity if it uses advanced patterns correctly. Does the evidence support this?

**Your Verdict:**
- If the code lacks production engineering (No CI/CD, No Docker) despite high complexity, lean towards the lower score (Level 3).
- If the code is small but architecturally perfect and robust, you can uphold the higher score (Level 4), but justify it heavily.
- Be fair but rigorous.

**Respond ONLY with valid JSON:**
{{
  "deliberation": "Briefly explain your thought process regarding the conflict.",
  "final_level": <int>,
  "judge_ruling": "A definitive, professional summary of your decision. Cite specific evidence used to break the tie.",
  "overruled_grader": <boolean>,
  "overruled_stats": <boolean>
}}
"""

    # 3. Call the Judge LLM
    # We use a slightly higher temperature (0.2) to allow for nuanced reasoning
    client = AsyncOpenAI(
        api_key=settings.GROQ_API_KEY, 
        base_url=settings.LLM_BASE_URL
    )

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a fair, wise, and highly technical judge. You value evidence over opinion."},
                {"role": "user", "content": case_file_prompt}
            ],
            temperature=0.2, 
            response_format={"type": "json_object"}
        )

        verdict_json = response.choices[0].message.content
        verdict = json.loads(verdict_json)

        # 4. Execute Judgment
        final_level = int(verdict.get("final_level", llm_level))
        ruling = verdict.get("judge_ruling", "Verdict affirmed.")
        deliberation = verdict.get("deliberation", "")
        
        print(f"👨‍⚖️ [Judge Agent] VERDICT REACHED: Level {final_level}")
        print(f"   💭 Deliberation: {deliberation[:150]}...")
        print(f"   📝 Ruling: {ruling}")
        
        # 5. Update State with the Final Verdict
        # We overwrite the level because this is the binding decision
        state["sfia_result"]["sfia_level"] = final_level
        state["sfia_result"]["level_name"] = _get_level_name(final_level)
        
        # We REPLACE the reasoning with the Judge's superior summary
        # This ensures the final certificate reflects the synthesized view
        state["sfia_result"]["reasoning"] = ruling
        
        # Add metadata for audit trails
        state["sfia_result"]["judge_intervened"] = True
        state["sfia_result"]["original_grader_level"] = llm_level
        state["sfia_result"]["original_stats_level"] = stats_level
        state["sfia_result"]["judge_deliberation"] = deliberation

    except Exception as e:
        print(f"❌ [Judge Agent] Mistrial: {str(e)}. Upholding Grader's decision.")
        state["errors"].append(f"Judge Agent failed: {str(e)}")
    
    return state

def _get_level_name(level: int) -> str:
    names = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
    return names.get(level, "Unknown")