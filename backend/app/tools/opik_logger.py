"""
Opik Integration
Tracing and logging for transparent AI decision-making
"""

from opik import Opik, track
from opik.evaluation import evaluate
from typing import Optional, Dict, Any
from functools import wraps
from app.core.config import settings


# Initialize Opik client
opik_client = Opik(
    api_key=settings.OPIK_API_KEY,
    workspace=settings.OPIK_WORKSPACE
)


def track_agent(agent_name: str):
    """
    Decorator to track agent execution with Opik
    
    Usage:
        @track_agent("validator")
        async def validate_repository(state):
            ...
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(state, *args, **kwargs):
            
            # Start Opik trace
            with opik_client.trace(
                name=f"{agent_name}_agent",
                tags=["agent", agent_name],
                metadata={
                    "job_id": state.get("job_id"),
                    "repo_url": state.get("repo_url"),
                    "current_step": agent_name
                }
            ) as trace:
                
                # Store trace ID in state
                if not state.get("opik_trace_id"):
                    state["opik_trace_id"] = trace.id
                
                # Execute agent
                result = await func(state, *args, **kwargs)
                
                # Log agent output
                trace.log_output({
                    "progress": result.get("progress"),
                    "errors": result.get("errors", []),
                    "agent_output": _get_agent_output(agent_name, result)
                })
                
                return result
        
        return wrapper
    
    return decorator


def _get_agent_output(agent_name: str, state: Dict) -> Dict[str, Any]:
    """
    Extract relevant output from state for each agent
    """
    
    outputs = {
        "validator": state.get("validation"),
        "scanner": {
            "ncrf": state.get("scan_metrics", {}).get("ncrf"),
            "markers": state.get("scan_metrics", {}).get("markers")
        },
        "grader": state.get("sfia_result"),
        "auditor": state.get("audit_result"),
        "reporter": {
            "final_credits": state.get("final_credits"),
            "certificate": state.get("certificate")
        }
    }
    
    return outputs.get(agent_name, {})


@track
async def track_llm_call(
    prompt: str,
    model: str,
    response: str,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Track individual LLM calls with Opik
    
    Usage:
        await track_llm_call(
            prompt="Assess this code...",
            model="gpt-4o",
            response='{"sfia_level": 4}',
            metadata={"confidence": 0.92}
        )
    """
    
    return {
        "prompt_length": len(prompt),
        "response_length": len(response),
        "model": model,
        "metadata": metadata or {}
    }


def log_decision_point(
    decision_name: str,
    input_data: Dict,
    output_decision: str,
    reasoning: str,
    metadata: Optional[Dict] = None
):
    """
    Log critical decision points (routing logic) to Opik
    
    Usage:
        log_decision_point(
            decision_name="should_proceed_to_scanner",
            input_data={"validation": {...}},
            output_decision="scanner",
            reasoning="Validation passed, repo size acceptable",
            metadata={"repo_size_kb": 45000}
        )
    """
    
    opik_client.log(
        name=decision_name,
        input=input_data,
        output={"decision": output_decision},
        metadata={
            "reasoning": reasoning,
            **(metadata or {})
        },
        tags=["decision", "routing"]
    )


async def evaluate_sfia_grading(
    ground_truth_level: int,
    predicted_level: int,
    repo_url: str
) -> Dict:
    """
    Evaluate SFIA grading accuracy using Opik
    
    This is useful for:
    - Testing against known repos
    - Improving the grading prompt
    - Demonstrating accuracy to judges
    
    Usage:
        # After manually verifying a repo should be Level 4
        await evaluate_sfia_grading(
            ground_truth_level=4,
            predicted_level=grader_result["sfia_level"],
            repo_url="https://github.com/user/repo"
        )
    """
    
    from opik.evaluation.metrics import Equals
    
    dataset = opik_client.create_dataset(
        name="sfia_ground_truth",
        description="Manually verified SFIA levels"
    )
    
    dataset.insert([{
        "input": {"repo_url": repo_url},
        "expected_output": {"sfia_level": ground_truth_level},
        "actual_output": {"sfia_level": predicted_level}
    }])
    
    # Evaluate
    results = evaluate(
        dataset=dataset,
        metrics=[Equals()]
    )
    
    return results


class OpikContextManager:
    """
    Context manager for tracking entire analysis workflow
    
    Usage:
        async with OpikContextManager(job_id, repo_url) as tracker:
            # All operations inside are traced
            await validator(state)
            await scanner(state)
            ...
    """
    
    def __init__(self, job_id: str, repo_url: str):
        self.job_id = job_id
        self.repo_url = repo_url
        self.trace = None
    
    async def __aenter__(self):
        self.trace = opik_client.trace(
            name="full_analysis_workflow",
            tags=["workflow", "full_pipeline"],
            metadata={
                "job_id": self.job_id,
                "repo_url": self.repo_url
            }
        ).__enter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.trace:
            if exc_type:
                self.trace.log_output({
                    "status": "failed",
                    "error": str(exc_val)
                })
            else:
                self.trace.log_output({
                    "status": "success"
                })
            
            self.trace.__exit__(exc_type, exc_val, exc_tb)
    
    def log_step(self, step_name: str, data: Dict):
        """Log intermediate steps"""
        if self.trace:
            self.trace.log(
                name=step_name,
                input=data.get("input", {}),
                output=data.get("output", {})
            )


