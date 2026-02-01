import asyncio
import sys
import os
import time
import json
import opik
from typing import Dict, Any

from opik.evaluation import evaluate
from opik import track
from opik.evaluation.metrics import Hallucination, BaseMetric, score_result

# App Imports
from app.evaluation.runner import SkillProtocolEvaluationRunner
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# 1. Custom Metrics (SFIA Accuracy)
# =========================================================

class SfiaAccuracyMetric(BaseMetric):
    """
    Checks if the predicted SFIA level matches the expected level.
    """
    def __init__(self, name="SFIA_Accuracy"):
        super().__init__(name=name)

    def score(self, expected_output: str, output: str, **kwargs) -> score_result.ScoreResult:
        """
        Args:
            expected_output: The expected SFIA level from the dataset (string or int).
            output: The reasoning/output string from the LLM.
            **kwargs: Extra data passed from the evaluation task (like sfia_result).
        """
        try:
            # 1. Parse Expected Level
            expected = int(expected_output)
            
            # 2. Parse Predicted Level
            # We prefer using the structured 'sfia_result' passed in kwargs if available
            sfia_result = kwargs.get("sfia_result", {}) 
            predicted = 0

            if sfia_result and "sfia_level" in sfia_result:
                predicted = int(sfia_result["sfia_level"])
            else:
                # Fallback: Try to parse generic JSON from the output string
                try:
                    clean = output.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean)
                    predicted = int(data.get("sfia_level", 0))
                except:
                    predicted = 0

            # 3. Score Logic
            if predicted == expected:
                return score_result.ScoreResult(
                    value=1.0, 
                    name=self.name, 
                    reason=f"Exact Match: Predicted L{predicted} == Expected L{expected}"
                )
            elif abs(predicted - expected) == 1:
                return score_result.ScoreResult(
                    value=0.5, 
                    name=self.name, 
                    reason=f"Close: Predicted L{predicted} vs Expected L{expected}"
                )
            else:
                return score_result.ScoreResult(
                    value=0.0, 
                    name=self.name, 
                    reason=f"Miss: Predicted L{predicted} vs Expected L{expected}"
                )
                
        except Exception as e:
            return score_result.ScoreResult(
                value=0.0, 
                name=self.name, 
                reason=f"Scoring Error: {str(e)}"
            )

# =========================================================
# 2. Main Execution
# =========================================================

async def main():
    # 1. Configure Environment
    # Ensure API Key is set for Opik's internal LLM calls (LiteLLM)
    if settings.OPENROUTER_API_KEY:
        os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY
    
    experiment_name = sys.argv[1] if len(sys.argv) > 1 else "OpenRouter-Migration-Test"
    
    # 2. Initialize Helper Classes
    runner = SkillProtocolEvaluationRunner()
    client = opik.Opik(project_name=settings.OPIK_PROJECT_NAME)

    # 3. Load Dataset
    print(f"📦 Fetching Dataset 'sfia-golden-v1'...")
    try:
        dataset = client.get_dataset(name="sfia-golden-v1")
        if not dataset:
             raise ValueError("Dataset not found")
    except Exception as e:
        print(f"❌ Dataset Error: {e}")
        print("💡 Tip: Run 'python -m app.scripts.run_feedback_loop' to create a dataset first.")
        return

    # 4. Define the Evaluation Task
    # This function wraps the complex async agent logic into a format Opik understands.
    @track(name="Evaluation Task", type="general") 
    def evaluation_task(dataset_item: Dict[str, Any]):
        """
        Takes a dataset item, runs the agent, and returns a dict mapping to metric arguments.
        """
        # Extract input from dataset item
        # Opik dataset items can be dicts or objects depending on SDK version/context
        repo_url = dataset_item.get("input")
        
        repo_name = repo_url.split('/')[-1] if repo_url else "unknown"
        print(f"🔄 Analyzing: {repo_name}")

        try:
            # Run the actual agents (using asyncio.run since evaluate() expects a sync function)
            # We create a unique job_id for this specific evaluation run
            job_id = f"eval_{repo_name}_{int(time.time())}"
            
            final_state = asyncio.run(runner.run_analysis_internal(
                repo_url=repo_url,
                job_id=job_id,
                model=settings.DEFAULT_MODEL 
            ))

            # Extract results from the agent state
            sfia_result = final_state.get("sfia_result", {})
            scan_metrics = final_state.get("scan_metrics", {})
            ncrf = scan_metrics.get("ncrf", {})
            validation = final_state.get("validation_result", {})
            
            # Prepare the "output" string (usually the reasoning)
            reasoning = sfia_result.get("reasoning") or "No reasoning provided."
            
            # Prepare context string for Hallucination metric
            context_str = (
                f"Data: SLOC={ncrf.get('total_sloc')}, "
                f"Complexity={ncrf.get('total_complexity')}, "
                f"Markers={scan_metrics.get('markers', {})}. "
                f"Bayesian Estimate: {validation.get('bayesian_best_estimate')}"
            )

            # RETURN DICT KEYS MUST MATCH METRIC .score() ARGUMENTS
            return {
                "input": repo_url,          # For Hallucination metric
                "output": reasoning,        # For Hallucination/SfiaAccuracy metrics
                "context": [context_str],   # For Hallucination metric
                "sfia_result": sfia_result, # For SfiaAccuracy metric (via kwargs)
                # Map dataset's expected output to the metric's argument name
                "expected_output": dataset_item.get("expected_output") 
            }

        except Exception as e:
            print(f"❌ Error processing {repo_name}: {e}")
            return {
                "input": repo_url, 
                "output": f"Error: {str(e)}", 
                "context": [], 
                "sfia_result": {},
                "expected_output": "0"
            }

    # 5. Configure Metrics
    
    # Hallucination Metric (LLM-as-a-Judge)
    hallucination_metric = Hallucination(
        name="Hallucination_Check",
        model="openrouter/google/gemini-2.0-flash-001" 
    )

    # Accuracy Metric (Heuristic/Custom)
    accuracy_metric = SfiaAccuracyMetric(name="Accuracy")

    eval_metrics = [accuracy_metric, hallucination_metric]

    # 6. Start Evaluation
    print(f"\n🚀 Starting Experiment: {experiment_name}")
    
    evaluate(
        dataset=dataset,
        task=evaluation_task,
        scoring_metrics=eval_metrics,
        experiment_name=experiment_name,
        task_threads=1, # Keep strictly 1 to avoid Rate Limits/Async loop conflicts
        project_name=settings.OPIK_PROJECT_NAME
    )

if __name__ == "__main__":
    asyncio.run(main())