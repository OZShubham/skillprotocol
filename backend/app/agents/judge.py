"""
Judge Agent (Supreme Court - ROBUST & FAIR)
Deliberates using Syntax, Semantics, Forensics, and History.
"""

import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.state import AnalysisState, get_progress_for_step
from app.core.opik_config import track_agent

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
    markers = scan_metrics.get("markers", {})
    semantic_report = scan_metrics.get("semantic_report", {}) # Expert Witness
    quality_report = scan_metrics.get("quality_report", {})   # Forensics
    git_stats = scan_metrics.get("git_stats", {})             # Maturity

    llm_level = int(sfia_result.get("sfia_level", 0))
    stats_level = int(validation_result.get("bayesian_best_estimate", 0))
    stats_conf = validation_result.get("confidence", 0.0)

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

    case_file_prompt = f"""
You are the Supreme Technical Arbiter for the SkillProtocol Certification Board.
Your goal is to distinguish between "Skill" (Code Quality) and "Process" (Engineering Maturity).

**CASE # {state.get('job_id', 'UNKNOWN')}**

**The Conflict:**
* **Assessor A (Grader Agent):** Recommends **Level {llm_level}** ({sfia_result.get('level_name')})
  * Argument: "{sfia_result.get('reasoning')}"
  * Confidence: {sfia_result.get('confidence', 0):.1%}

* **Assessor B (Statistical Model):** Suggests **Level {stats_level}**
  * Reasoning: "{validation_result.get('reasoning')}"
  * Confidence: {stats_conf:.1%}

**The Evidence:**
1. **Scale:** {ncrf.get('total_sloc')} lines of code. Complexity: {ncrf.get('total_complexity')}.
2. **Process Maturity (Time):** {maturity_context}
3. **Forensic Analysis (Patterns):** {quality_forensics}
4. **Expert Testimony (Semantic Meaning):** {expert_testimony}

**Deliberation Instructions (STRICT & FAIR):**

1. **The "Lone Wolf" Fairness Rule:**
   - If the Code Quality is HIGH (Semantic Score > 7, Good Forensics), but it is a "One-Shot Push" (1-2 commits), do NOT punish the user to Level 1.
   - **Ruling:** Acknowledge the coding skill. You may award up to **Level 3 (Apply)**.
   - **Restriction:** Do NOT award Level 4 (Enable) or 5 (Ensure). These levels *require* proven lifecycle management (CI/CD, history, iterative maintenance) which is missing here.

2. **The "Code Dump" Check:**
   - If code is complex but Semantic Review says "Generic logic" or "Unrelated files", AND it's a One-Shot Push, this is likely a copy-paste dump. Downgrade to **Level 1** or **Level 2**.

3. **Level 5 Requirement:**
   - To verify Level 5 (Ensure), you need High Code Quality AND Proven Process (History > 1 week, CI/CD, Tests). Missing any of these caps the score at Level 4.

4. **Resolve the Conflict:**
   - Use the Expert Testimony to break ties. If the LLM Reviewer loves the code, lean towards the Grader's score (subject to the Maturity Cap).

**Respond ONLY with valid JSON:**
{{
  "deliberation": "Explain your decision. Explicitly mention if you capped the score due to lack of history.",
  "final_level": <int>,
  "judge_ruling": "Definitive verdict statement.",
  "overruled_grader": <boolean>,
  "overruled_stats": <boolean>
}}
"""

    # 3. Call the Judge LLM
    client = AsyncOpenAI(
        api_key=settings.GROQ_API_KEY, 
        base_url=settings.LLM_BASE_URL
    )

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a fair, wise, and highly technical judge."},
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
        print(f"   💭 Reasoning: {deliberation[:100]}...")
        
        # 5. Update State with the Final Verdict
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