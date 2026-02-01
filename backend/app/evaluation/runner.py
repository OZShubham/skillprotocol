import os
import asyncio
from typing import Dict, Any, Optional
from opik import track

# App Imports
from app.core.opik_config import OpikManager, PROJECTS
from app.core.config import settings

class SkillProtocolEvaluationRunner:
    """
    The engine that runs your agents specifically for evaluation purposes.
    Routes traces to the 'evals' project to keep production data clean.
    """
    
    def __init__(self):
        # 1. Setup Opik Project (Route to 'evals' project, not production)
        self.project_name = PROJECTS["eval"]
        self.client = OpikManager.get_client(self.project_name)

        # 2. Ensure OpenRouter Key is available for Opik/LiteLLM internals
        if not os.getenv("OPENROUTER_API_KEY") and settings.OPENROUTER_API_KEY:
            os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY
            print(f"🔑 Configured Evaluation Runner with OpenRouter Key")
    
    @track(name="Repository Analysis", type="tool")
    async def run_analysis_internal(
        self, 
        repo_url: str, 
        job_id: str, 
        model: str = None
    ) -> Dict[str, Any]:
        """
        Executes the actual Agent Graph for a single repository.
        This function is called by the evaluation loop.
        """
        # Lazy import to avoid circular dependency issues
        from app.agents.graph import run_analysis
        
        print(f"   --> Runner invoking Graph for: {repo_url}")
        
        # Run the agent graph
        # Note: The agents will use the models defined in settings.py (OpenRouter)
        try:
            state = await run_analysis(
                repo_url=repo_url,
                user_id="eval_bot",
                job_id=job_id,
                user_github_token=None 
            )
            return state
            
        except Exception as e:
            print(f"   ❌ Runner Error: {e}")
            # Return a minimal error state to prevent evaluation crash
            return {
                "errors": [str(e)],
                "sfia_result": {},
                "scan_metrics": {},
                "validation_result": {}
            }