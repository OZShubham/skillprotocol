from langchain_core.tools import tool
from app.schemas.mentor import GrowthPlan

@tool(args_schema=GrowthPlan)
def submit_growth_plan(
    current_assessment,
    next_level_requirements,
    actionable_roadmap,
    quick_wins,
    credit_projection
):
    """
    Submits the final personalized growth plan for the developer.
    Call this tool ONLY after you have analyzed the codebase and identified all requirements.
    """
    # This return value tells the Agent that the action was successful
    return {
        "status": "success",
        "plan_summary": f"Plan created with {len(quick_wins)} quick wins."
    }