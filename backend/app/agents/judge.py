"""
Judge Agent (Supreme Court) - FIXED
Deliberates using Syntax, Semantics, Forensics, and History.
Now fetches the "Constitution" (Prompt) from the Opik Library.
"""

import json
import logging
from openai import AsyncOpenAI
from opik import opik_context

from app.core.config import settings
from app.core.state import AnalysisState, get_progress_for_step
from app.core.opik_config import track_agent, OpikManager, MAIN_PROJECT

logger = logging.getLogger(__name__)

@track_agent(name="Judge Agent", agent_type="llm")
async def arbitrate_level(state: AnalysisState) -> AnalysisState:
    """
    Agent 4.5: The Supreme Judge
    
    Responsibilities:
    1. Review the entire case file (Grader + Stats + Semantics + History).
    2. Deliberate on conflicts using Chain of Thought.
    3. Issue a final, binding verdict with detailed justification.
    """
    
    state["current_step"] = "judge"
    state["progress"] = get_progress_for_step("judge")
    
    # 1. Gather Evidence
    sfia_result = state.get("sfia_result")
    validation_result = state.get("validation_result")
    scan_metrics = state.get("scan_metrics", {})
    
    # Fail-safe: If critical data is missing, we cannot judge properly
    if not sfia_result or not validation_result:
        print("⚖️ [Judge Agent] Missing assessment data. Skipping review.")
        return state

    # Extract all evidence layers
    ncrf = scan_metrics.get("ncrf", {})
    semantic_report = scan_metrics.get("semantic_report", {}) # Expert Witness
    quality_report = scan_metrics.get("quality_report", {})   # Forensics
    git_stats = scan_metrics.get("git_stats", {})             # Maturity

    llm_level = int(sfia_result.get("sfia_level", 0))
    stats_level = int(validation_result.get("bayesian_best_estimate", 0))
    
    print(f"👨‍⚖️ [Judge Agent] Deliberating Case. Grader: {llm_level} | Stats: {stats_level}")

    # 2. Construct the "Deliberation" Case File
    
    # Layer 1: Expert Testimony (Semantics)
    expert_testimony = "No semantic review available."
    if semantic_report:
        expert_testimony = f"""
        - **Reviewer Insight:** "{semantic_report.get('key_insight', 'N/A')}"
        - **Code Quality Score:** {semantic_report.get('average_score', 0)}/10
        - **Identified Strengths:** {', '.join(semantic_report.get('key_strengths', [])[:2])}
        - **Identified Weaknesses:** {', '.join(semantic_report.get('key_weaknesses', [])[:2])}
        """
        
    # Layer 2: Forensics (Patterns)
    quality_forensics = "No quality analysis available."
    if quality_report:
        quality_forensics = f"""
        - **Sophistication:** {quality_report.get('sophistication', 'basic')}
        - **Red Flags (Anti-Patterns):** {quality_report.get('red_flags_count', 0)}
        - **Green Flags (Best Practices):** {quality_report.get('green_flags_count', 0)}
        """

    # Layer 3: Process Maturity (Time Dimension)
    maturity_context = "No git history available."
    is_one_shot_push = False
    
    if git_stats:
        commits = git_stats.get('commit_count', 0)
        days = git_stats.get('days_active', 0)
        stability = git_stats.get('stability_score', 0.5)
        
        # Heuristic for "One Shot Push": Low commits (<3)
        is_one_shot_push = (commits <= 2 and days < 1)
        
        maturity_context = f"""
        - **Commit Count:** {commits}
        - **Days Active:** {days}
        - **Stability Score:** {stability:.2f}
        - **One-Shot Push Detected:** {is_one_shot_push}
        """

    # 3. Fetch the "Constitution" from Opik Prompt Library (Best Use of Opik)
    # This allows you to edit the Judge's logic in the UI without redeploying
    try:
        client = OpikManager.get_client(MAIN_PROJECT)
        # Try to fetch, if it doesn't exist, create it (Self-Healing)
        prompt_obj = client.get_prompt(name="supreme-court-judge-rules")
        
        if not prompt_obj:
            # Fallback / Init
            base_prompt = """
You are the Supreme Technical Arbiter for the SkillProtocol Certification Board.
Your goal is to distinguish between "Skill" (Code Quality) and "Process" (Engineering Maturity).

**CASE # {{job_id}}**

**The Conflict:**
* **Assessor A (Grader Agent):** Recommends **Level {{llm_level}}**
* **Assessor B (Statistical Model):** Suggests **Level {{stats_level}}**

**The Evidence:**
1. **Scale:** {{sloc}} lines of code. Complexity: {{complexity}}.
2. **Process Maturity:** {{maturity_context}}
3. **Forensics:** {{quality_forensics}}
4. **Expert Testimony:** {{expert_testimony}}

**Deliberation Instructions:**

1. **The "Lone Wolf" Rule:**
   - If Code Quality is HIGH but it is a "One-Shot Push" (<3 commits), CAP at Level 3.
   - Do NOT award Level 4/5 without proven lifecycle management.

2. **The "Code Dump" Check:**
   - If code is complex but looks like a generic dump, Downgrade to Level 1.

3. **Resolve the Conflict:**
   - Use Expert Testimony to break ties.

**Respond ONLY with valid JSON:**
{{
  "deliberation": "Explain your decision.",
  "final_level": <int>,
  "judge_ruling": "Definitive verdict statement.",
  "overruled_grader": <boolean>
}}
            """
            prompt_obj = client.create_prompt(name="supreme-court-judge-rules", prompt=base_prompt)
            print("🆕 Created 'supreme-court-judge-rules' prompt in library")
            
        # Use the prompt text
        system_prompt = prompt_obj.prompt
        
    except Exception as e:
        print(f"⚠️ Prompt Library Error: {e}. Using fallback.")
        system_prompt = "You are a Judge. Resolve the conflict between Level {{llm_level}} and {{stats_level}}."

    # 4. Format the Prompt
    # Using simple replacement for robustness
    formatted_prompt = system_prompt.replace("{{llm_level}}", str(llm_level))\
                                    .replace("{{stats_level}}", str(stats_level))\
                                    .replace("{{sloc}}", str(ncrf.get("total_sloc")))\
                                    .replace("{{complexity}}", str(ncrf.get("total_complexity")))\
                                    .replace("{{job_id}}", str(state.get("job_id")))\
                                    .replace("{{maturity_context}}", maturity_context)\
                                    .replace("{{quality_forensics}}", quality_forensics)\
                                    .replace("{{expert_testimony}}", expert_testimony)

    # 5. Call the Judge LLM
    client_llm = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.LLM_BASE_URL)

    try:
        response = await client_llm.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a fair, wise, and highly technical judge."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.2, # Low temp for consistent verdicts
            response_format={"type": "json_object"}
        )

        verdict_json = response.choices[0].message.content
        verdict = json.loads(verdict_json)

        # 6. Execute Judgment
        final_level = int(verdict.get("final_level", llm_level))
        ruling = verdict.get("judge_ruling", "Verdict affirmed.")
        deliberation = verdict.get("deliberation", "")
        
        print(f"👨‍⚖️ [Judge Agent] VERDICT REACHED: Level {final_level}")
        print(f"   💭 Reasoning: {deliberation[:100]}...")
        
        # 7. Log to Opik (Best Use of Opik)
        opik_context.update_current_trace(
            metadata={
                "judge_deliberation": deliberation,
                "judge_verdict": final_level,
                "overruled_grader": verdict.get("overruled_grader", False)
            }
        )
        
        # 8. Update State with the Final Verdict
        state["sfia_result"]["sfia_level"] = final_level
        state["sfia_result"]["level_name"] = _get_level_name(final_level)
        state["sfia_result"]["reasoning"] = ruling
        state["sfia_result"]["judge_intervened"] = True
        state["sfia_result"]["judge_deliberation"] = deliberation

    except Exception as e:
        print(f"❌ [Judge Agent] Mistrial: {str(e)}")
        state["errors"].append(f"Judge Agent failed: {str(e)}")
    
    return state

def _get_level_name(level: int) -> str:
    names = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
    return names.get(level, "Unknown")