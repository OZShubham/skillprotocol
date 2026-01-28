from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class CurrentAssessment(BaseModel):
    strengths: List[str] = Field(description="List of identified strengths in the codebase")
    weaknesses: List[str] = Field(description="List of identified gaps or weaknesses")
    current_level_justification: str = Field(description="Why the developer is at their current SFIA level")

class NextLevelRequirements(BaseModel):
    missing_technical_skills: List[str] = Field(description="Technical skills that need to be added")
    missing_architectural_patterns: List[str] = Field(description="Design patterns or architectural concepts to learn")
    missing_best_practices: List[str] = Field(description="Best practices that should be implemented")
    estimated_effort_hours: float = Field(description="Estimated hours to reach next level")

class ActionItem(BaseModel):
    step_number: int
    action: str
    impact_on_credits: Literal["high", "medium", "low"]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    estimated_time: str
    resources: List[str] = Field(description="Links or resources to learn this skill")

class CreditProjection(BaseModel):
    current_credits: float
    potential_credits_after_improvements: float
    percentage_increase: float

class GrowthPlan(BaseModel):
    """The complete growth plan structure."""
    current_assessment: CurrentAssessment
    next_level_requirements: NextLevelRequirements
    actionable_roadmap: List[ActionItem]
    quick_wins: List[str] = Field(description="Easy changes that can boost credits immediately (< 1 day effort)")
    credit_projection: CreditProjection