# backend/app/core/opik_config.py
import opik
from opik import Opik
from functools import wraps
from app.core.config import settings

# CORRECT: Dynamic reference to settings, not a hardcoded string
MAIN_PROJECT = settings.OPIK_PROJECT_NAME 

PROJECTS = {
    "main": MAIN_PROJECT,
    "eval": MAIN_PROJECT,
    "optimizer": MAIN_PROJECT
}

class OpikManager:
    _instances = {}
    
    @classmethod
    def get_client(cls, project: str = None) -> Opik:
        # Default to the configured main project
        target_project = project or MAIN_PROJECT
        
        if target_project not in cls._instances:
            cls._instances[target_project] = Opik(
                project_name=target_project,
                api_key=settings.OPIK_API_KEY,
                workspace=settings.OPIK_WORKSPACE
            )
        
        return cls._instances[target_project]

def track_agent(
    name: str,
    agent_type: str = "tool",
    project: str = None,
    tags: list = None
):
    """
    Decorator that explicitly passes the project name from settings.
    This prevents Opik from falling back to 'Default Project'.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Resolve project from settings if not provided
            target_project = project or MAIN_PROJECT
            
            # 2. Ensure client is initialized
            OpikManager.get_client(target_project)
            
            # 3. Explicitly pass project_name to the native tracker
            tracked_func = opik.track(
                name=name,
                type=agent_type,
                project_name=target_project, # <--- The Fix: Explicit passing
                tags=tags or []
            )(func)
            
            result = await tracked_func(*args, **kwargs)
            return result
        
        return wrapper
    return decorator

# Helpers remain the same, but now use the dynamic MAIN_PROJECT
def log_to_main_project(name: str, input_data: dict, output_data: dict, metadata: dict = None):
    client = OpikManager.get_client(MAIN_PROJECT)
    client.trace(
        name=name,
        input=input_data,
        output=output_data,
        tags=["production", "main"],
        metadata=metadata or {}
    )

def log_evaluation_trace(name: str, input_data: dict, output_data: dict, metrics: dict):
    client = OpikManager.get_client(MAIN_PROJECT)
    client.trace(
        name=name,
        input=input_data,
        output=output_data,
        tags=["evaluation"],
        metadata={**metrics, "experiment_type": "evaluation"}
    )