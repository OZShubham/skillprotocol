"""
SkillProtocol - Opik-Native Evaluation CLI with Groq
Usage: python run_evaluation.py [experiment_name] [limit]
"""
import asyncio
import sys
import os
from opik import Opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import AgentTaskCompletionJudge, Hallucination

# App Imports
from app.evaluation.runner import SkillProtocolEvaluationRunner
from app.core.config import settings

async def main():
    # Set Groq API key
    os.environ["GROQ_API_KEY"] = "your-groq-api-key"
    
    # 1. Configuration
    experiment_name = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    runner = SkillProtocolEvaluationRunner()
    client = Opik(project_name=settings.OPIK_PROJECT_NAME)

    # 2. Sync Dataset
    print(f"📦 Syncing Golden Dataset to Opik...")
    dataset = await runner.create_opik_dataset()

    # 3. Define the Native Task
    async def evaluation_task(dataset_item):
        """
        Executes the agentic graph for a single repository.
        The keys in the return dict MUST match the metric inputs.
        """
        repo_url = dataset_item["repo_url"]
        
        # Run the production graph (Agent Handoff) with Groq models
        final_state = await runner.run_analysis_internal(
            repo_url=repo_url,
            job_id=f"eval_{experiment_name}_{repo_url.split('/')[-1]}",
            model="groq/llama3-70b-8192"  # Pass Groq model to your runner
        )
        
        return {
            "input": repo_url,
            "output": str(final_state.get("sfia_result", {})),
            "context": str(final_state.get("scan_metrics", {})),
            "expected_output": dataset_item.get("expected_sfia_level", "")  # For metrics
        }

    # 4. Define Metrics with Groq models
    metrics = [
        AgentTaskCompletionJudge(
            name="SFIA Accuracy",
            model="groq/llama3-70b-8192"  # Use Groq for evaluation
        ),
        Hallucination(
            model="groq/llama3-70b-8192"  # Use Groq for hallucination detection
        )
    ]

    # 5. Run Experiment
    print(f"🚀 Starting Experiment: {experiment_name} (Powered by Groq)")
    result = evaluate(
        dataset=dataset,
        task=evaluation_task,
        scoring_metrics=metrics,
        experiment_name=experiment_name,
        nb_samples=limit,
        experiment_config={
            "model_provider": "groq",
            "primary_model": "llama3-70b-8192",
            "evaluation_framework": "opik"
        }
    )

    # 6. Results Summary
    print(f"\n🏆 EVALUATION RESULTS")
    print(f"Experiment: {experiment_name}")
    print(f"Samples processed: {len(result.test_results)}")
    
    # Print aggregated scores
    scores = result.aggregate_evaluation_scores()
    for metric_name, stats in scores.aggregated_scores.items():
        print(f"{metric_name}: {stats.mean:.3f} (±{stats.std:.3f})")

    # 7. Final Dashboard Link
    dashboard_url = f"https://www.comet.com/{settings.OPIK_WORKSPACE}/opik/projects/{settings.OPIK_PROJECT_NAME}/experiments"
    print(f"\n✅ Evaluation complete!")
    print(f"📊 Compare versions here:\n🔗 {dashboard_url}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Eval failed: {e}")
