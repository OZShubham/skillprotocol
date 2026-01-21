# ============================================================================
# FILE: backend/app/core/opik_config.py
# ============================================================================
"""
Centralized Opik Configuration
This ensures ALL traces go to the same project
"""

import opik
from opik import Opik
from functools import wraps
from app.core.config import settings

# ============================================================================
# CONFIGURATION
# ============================================================================

MAIN_PROJECT = "skillprotocol"

PROJECTS = {
    "main": MAIN_PROJECT,
    "eval": MAIN_PROJECT,
    "optimizer": MAIN_PROJECT
}

# ============================================================================
# SINGLETON CLIENT
# ============================================================================

class OpikManager:
    _instances = {}
    
    @classmethod
    def get_client(cls, project: str = None) -> Opik:
        # If no project specified, OR if it's one of the old separate ones, 
        # force usage of MAIN_PROJECT.
        target_project = MAIN_PROJECT
        
        if target_project not in cls._instances:
            cls._instances[target_project] = Opik(
                project_name=target_project,
                api_key=settings.OPIK_API_KEY,
                workspace=settings.OPIK_WORKSPACE
            )
        
        return cls._instances[target_project]

# ============================================================================
# DECORATOR WITH CORRECT PROJECT
# ============================================================================

def track_agent(
    name: str,
    agent_type: str = "tool",
    project: str = None,
    tags: list = None
):
    """
    Custom track decorator that ensures correct project routing.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Ensure we use the main project
            target_project = MAIN_PROJECT
            OpikManager.get_client(target_project)
            
            # Apply opik.track dynamically
            tracked_func = opik.track(
                name=name,
                type=agent_type,
                project_name=target_project,
                tags=tags or []
            )(func)
            
            result = await tracked_func(*args, **kwargs)
            return result
        
        return wrapper
    return decorator

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_to_main_project(name: str, input_data: dict, output_data: dict, metadata: dict = None):
    """
    Manually log a trace to the main project
    """
    client = OpikManager.get_client(MAIN_PROJECT)
    
    # Log trace to the unified project
    client.trace(
        name=name,
        input=input_data,
        output=output_data,
        tags=["production", "main"],
        metadata=metadata or {}
    )

def log_evaluation_trace(name: str, input_data: dict, output_data: dict, metrics: dict):
    """
    Log evaluation traces to the main project (tagged as evaluation)
    """
    client = OpikManager.get_client(MAIN_PROJECT)
    
    client.trace(
        name=name,
        input=input_data,
        output=output_data,
        tags=["evaluation"],  # Use tags to distinguish, not project
        metadata={
            **metrics,
            "experiment_type": "evaluation"
        }
    )