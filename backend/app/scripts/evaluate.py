import os
from opik import Opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import AgentTaskCompletionJudge

# 1. Setup - use your existing environment config
client = Opik(project_name="skillprotocol")

def evaluation_task(dataset_item):
    """
    Bridge: This function should call your actual agent.
    """
    # Simulate calling your Grader Agent
    # final_state = await run_analysis(dataset_item["repo_url"])
    return {
        "output": f"SFIA Level: 3. Reasoning: Modular structure found.", # Replace with agent output
        "input": dataset_item["repo_url"]
    }

# 2. Define Metric
metrics = [AgentTaskCompletionJudge()]

# 3. Run
if __name__ == "__main__":
    dataset = client.get_dataset(name="sfia-golden-v1")
    evaluate(
        experiment_name="baseline_check",
        dataset=dataset,
        task=evaluation_task,
        scoring_metrics=metrics
    )