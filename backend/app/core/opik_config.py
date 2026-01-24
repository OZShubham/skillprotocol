# # backend/app/core/opik_config.py
# import opik
# from opik import Opik
# from functools import wraps
# from app.core.config import settings

# MAIN_PROJECT = settings.OPIK_PROJECT_NAME


# class OpikManager:
#     _instance = None

#     @classmethod
#     def get_client(cls, project_name: str = MAIN_PROJECT) -> opik.Opik:
#         """
#         Returns a singleton Opik client.
#         """
#         if cls._instance is None:
#             print(f"🔌 Initializing Opik Client for project: {project_name}")
            
#             # ✅ CORRECT for Opik 0.1.96: Use 'host' parameter
#             cls._instance = opik.Opik(
#                 project_name=project_name,
#                 api_key=settings.OPIK_API_KEY,
#                 workspace=settings.OPIK_WORKSPACE,
#                 host="https://www.comet.com/opik/api"  # ← CORRECT parameter name
#             )
            
#         return cls._instance


# def track_agent(
#     name: str,
#     agent_type: str = "tool",
#     project: str = None,
#     tags: list = None
# ):
#     """Decorator that tracks agent execution"""
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             target_project = project or MAIN_PROJECT
#             OpikManager.get_client(target_project)
            
#             tracked_func = opik.track(
#                 name=name,
#                 type=agent_type,
#                 project_name=target_project,
#                 tags=tags or []
#             )(func)
            
#             result = await tracked_func(*args, **kwargs)
#             return result
        
#         return wrapper
#     return decorator


# def log_to_main_project(name: str, input_data: dict, output_data: dict, metadata: dict = None):
#     client = OpikManager.get_client(MAIN_PROJECT)
#     client.trace(
#         name=name,
#         input=input_data,
#         output=output_data,
#         tags=["production", "main"],
#         metadata=metadata or {}
#     )


# def log_evaluation_trace(name: str, input_data: dict, output_data: dict, metrics: dict):
#     client = OpikManager.get_client(MAIN_PROJECT)
#     client.trace(
#         name=name,
#         input=input_data,
#         output=output_data,
#         tags=["evaluation"],
#         metadata={**metrics, "experiment_type": "evaluation"}
#     )





# backend/app/core/opik_config.py
import opik
from opik import Opik
from functools import wraps
from app.core.config import settings

# 1. Define Project Routing (Critical for Evaluation/Optimization)
# This separates your production traces from your experimental optimization runs
PROJECTS = {
    "main": settings.OPIK_PROJECT_NAME,
    "eval": f"{settings.OPIK_PROJECT_NAME}-evals",
    "optimizer": f"{settings.OPIK_PROJECT_NAME}-optimizer"
}

MAIN_PROJECT = settings.OPIK_PROJECT_NAME

class OpikManager:
    _instance = None
    _clients = {}

    @classmethod
    def get_client(cls, project_name: str = MAIN_PROJECT) -> opik.Opik:
        """
        Returns a singleton Opik client for a specific project.
        """
        if project_name not in cls._clients:
            print(f"🔌 Initializing Opik Client for project: {project_name}")
            
            cls._clients[project_name] = opik.Opik(
                project_name=project_name,
                api_key=settings.OPIK_API_KEY,
                workspace=settings.OPIK_WORKSPACE,
                host="https://www.comet.com/opik/api"
            )
            
        return cls._clients[project_name]

def track_agent(
    name: str,
    agent_type: str = "tool",
    project: str = None,
    tags: list = None
):
    """Decorator that tracks agent execution"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            target_project = project or MAIN_PROJECT
            # Ensure client exists
            OpikManager.get_client(target_project)
            
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

def log_to_main_project(name: str, input_data: dict, output_data: dict, metadata: dict = None):
    client = OpikManager.get_client(MAIN_PROJECT)
    client.trace(
        name=name,
        input=input_data,
        output=output_data,
        tags=["production", "main"],
        metadata=metadata or {}
    )


def log_evaluation_trace(name: str, input_data: dict, output_data: dict, scores: dict, experiment_name: str, model_info: dict = None):
    """Logs an evaluation run to the specific Eval project"""
    client = OpikManager.get_client(PROJECTS["eval"])
    
    # Format scores for Opik
    feedback_scores = [
        {"name": k, "value": v} for k, v in scores.items()
    ]

    client.trace(
        name=name,
        input=input_data,
        output=output_data,
        feedback_scores=feedback_scores,
        tags=["evaluation", experiment_name],
        metadata={
            "experiment_name": experiment_name,
            "model_info": model_info or {}
        }
    )