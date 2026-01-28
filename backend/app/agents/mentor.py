import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# App Imports
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent
from app.utils.sse import push_live_log
from app.tools.mentor_tools import submit_growth_plan

logger = logging.getLogger(__name__)

@track_agent(name="Mentor Agent", agent_type="llm", tags=["mentorship", "tool-use"])
async def provide_mentorship(state: AnalysisState) -> AnalysisState:
    """
    Agent 7: Mentor (Growth Advisor) using Groq with Native Tool Binding.
    """
    job_id = state["job_id"]
    state["current_step"] = "mentor"
    state["progress"] = get_progress_for_step("mentor")
    
    push_live_log(job_id, "mentor", "🎓 Reviewing your career trajectory...", "success")

    # 1. Initialize Groq Model
    # ChatGroq supports bind_tools() natively!
    try:
        llm = ChatGroq(
            model=settings.LLM_MODEL,  # e.g. "llama-3.3-70b-versatile"
            api_key=settings.GROQ_API_KEY,
            temperature=0.7
        )
    except Exception as e:
        logger.error(f"Failed to init ChatGroq: {e}")
        state["errors"].append(f"Mentor Init Failed: {str(e)}")
        return state

    # 2. Bind Tools (Native Groq Support)
    # This effectively "gives" the tool to the LLM
    tools = [submit_growth_plan]
    llm_with_tools = llm.bind_tools(tools)
    
    # 3. Create Context
    context_str = _build_mentor_context(state) 

    # 4. Define Persona
    system_prompt = """You are a Senior Technical Mentor. 
    Analyze the developer's profile and code metrics.
    
    Your Goal: Create a detailed Growth Plan to help them level up.
    
    Process:
    1. Think deeply about their gaps (Reasoning).
    2. Construct a valid Growth Plan object matching the schema.
    3. Call the 'submit_growth_plan' tool to finalize your advice.
    """

    # 5. Invoke the Model
    # Groq will return a tool_call in the response if it decides to use the tool
    try:
        response = await llm_with_tools.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context_str)
        ])
    except Exception as e:
        logger.error(f"Mentor LLM Call Failed: {e}")
        state["errors"].append(f"Mentor Inference Failed: {str(e)}")
        return state

    # 6. Process the Output (Agentic Decision Handling)
    if response.tool_calls:
        # The Agent DECIDED to call the tool
        tool_call = response.tool_calls[0]
        if tool_call["name"] == "submit_growth_plan":
            # LangChain automatically parses the JSON arguments for you
            growth_plan_data = tool_call["args"]
            
            logger.info(f"[Mentor] Groq Agent autonomously generated plan")
            push_live_log(job_id, "mentor", "✅ Roadmap generated via Groq Tool Use", "success")
            
            # Store result directly in state
            state["mentorship_plan"] = growth_plan_data
            return state

    # Fallback if Agent decided NOT to call the tool
    logger.warning("[Mentor] Agent did not call submit tool. Using raw content.")
    state["errors"].append("Mentor Agent failed to submit structured plan.")
    return state

def _build_mentor_context(state: AnalysisState) -> str:
    """Helper to extract clean string context from state"""
    sfia = state.get("sfia_result", {})
    ncrf = state.get("scan_metrics", {}).get("ncrf", {})
    markers = state.get("scan_metrics", {}).get("markers", {})
    
    return f"""
    Current SFIA Level: {sfia.get('sfia_level')}
    Verified Credits: {state.get('final_credits')}
    
    Strengths Identified: {sfia.get('evidence', [])}
    Gaps identified by Grader: {sfia.get('missing_for_next_level', [])}
    
    Codebase Stats:
    - SLOC: {ncrf.get('total_sloc')}
    - Complexity: {ncrf.get('total_complexity')}
    - Main Language: {ncrf.get('dominant_language')}
    
    Capabilities Detected:
    - Tests: {markers.get('has_tests')}
    - CI/CD: {markers.get('has_ci_cd')}
    - Docker: {markers.get('has_docker')}
    """