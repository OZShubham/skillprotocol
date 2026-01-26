import asyncio
import sys
import os
import json
import opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import Hallucination, AnswerRelevance

# Your Custom Task Span Metric
from app.evaluation.custom_metrics import BayesianAlignmentMetric
from app.evaluation.runner import SkillProtocolEvaluationRunner
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

async def main():
    # 1. Setup Environment - Gemini Configuration
    if hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY:
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
    elif hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
        os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
    else:
        raise ValueError("Please set GOOGLE_API_KEY or GEMINI_API_KEY in your environment")
    
    experiment_name = sys.argv[1] if len(sys.argv) > 1 else "baseline-v1"
    
    runner = SkillProtocolEvaluationRunner()
    client = opik.Opik(project_name="skillprotocol-evals")

    # 2. Pull the Golden Dataset and Debug
    print(f"📦 Fetching Golden Dataset: sfia-golden-v1...")
    try:
        dataset = client.get_dataset(name="sfia-golden-v1")
        
        # DEBUG: Check what's actually in the dataset
        dataset_items = list(dataset.get_items())
        print(f"✅ Dataset loaded with {len(dataset_items)} items")
        
        print(f"\n📊 Dataset Contents:")
        for i, item in enumerate(dataset_items):
            if hasattr(item, 'input') and hasattr(item, 'expected_output'):
                repo_url = item.input
                expected_level = item.expected_output
            else:
                repo_url = item.get("input", "Unknown")
                expected_level = item.get("expected_output", "Unknown")
            
            print(f"  [{i+1}] {repo_url} -> Level {expected_level}")
        
        # Ask user if they want to continue with this dataset
        if len(dataset_items) == 0:
             print("❌ Dataset is empty. Please run 'python -m app.scripts.run_feedback_loop' or create the dataset first.")
             return

    except Exception as e:
        print(f"❌ Dataset not found: {e}")
        print("💡 Make sure 'sfia-golden-v1' exists in your Opik workspace")
        return

    # 3. Define the Evaluation Task
    from opik import track
    
    @track(name="SFIA Repository Analysis", type="task")
    def evaluation_task(dataset_item): 
        """
        This task MUST be decorated with @track and MUST be synchronous
        """
        if hasattr(dataset_item, 'input') and hasattr(dataset_item, 'expected_output'):
            repo_url = dataset_item.input
            expected_sfia_level = int(dataset_item.expected_output)
        else:
            repo_url = dataset_item["input"]
            expected_sfia_level = int(dataset_item["expected_output"])
            
        repo_name = repo_url.split('/')[-1]
        
        print(f"🔄 Processing: {repo_name} (Expected Level: {expected_sfia_level})")
        
        try:
            # Use asyncio.run to call the async function from sync context
            final_state = asyncio.run(runner.run_analysis_internal(
                repo_url=repo_url,
                job_id=f"eval_{repo_name}",
                model="gemini/gemini-2.0-flash"
            ))
            
            # Extract results for evaluation
            sfia_result = final_state.get("sfia_result", {})
            validation_result = final_state.get("validation_result", {})
            scan_metrics = final_state.get("scan_metrics", {})
            
            # --- FIX: PREPARE DATA FOR OPIK METRICS ---
            # 1. Determine the "Output" string (The reasoning text)
            agent_reasoning = sfia_result.get("reasoning", "No reasoning provided.")
            if sfia_result.get("judge_intervened"):
                agent_reasoning = sfia_result.get("judge_summary") or sfia_result.get("judge_justification") or agent_reasoning

            # 2. Determine "Context" (The evidence used)
            # We summarize metrics to avoid token limits
            ncrf = scan_metrics.get("ncrf", {})
            context_summary = (
                f"SLOC: {ncrf.get('total_sloc')}, "
                f"Complexity: {ncrf.get('total_complexity')}, "
                f"Bayesian Prior: Level {validation_result.get('bayesian_best_estimate')}"
            )

            # Return the complete analysis state mapped to standard keys
            return {
                # Standard keys for built-in Opik metrics (Hallucination, Relevance)
                "input": f"Analyze the repository {repo_url} and assign an SFIA level.",
                "output": agent_reasoning,
                "context": [context_summary],
                
                # Custom keys for your custom metrics (BayesianAlignmentMetric)
                "repo_url": repo_url,
                "repo_name": repo_name,
                "expected_sfia_level": expected_sfia_level,
                "sfia_result": sfia_result,
                "validation_result": validation_result,
                "scan_metrics": scan_metrics,
                "full_state": final_state
            }
            
        except Exception as e:
            print(f"❌ Error processing {repo_name}: {str(e)}")
            return {
                "input": repo_url,
                "output": f"Error: {str(e)}",
                "context": [],
                "repo_url": repo_url,
                "repo_name": repo_name,
                "expected_sfia_level": expected_sfia_level,
                "sfia_result": {},
                "validation_result": {},
                "scan_metrics": {},
                "error": str(e)
            }

    # 4. Initialize Metrics
    print(f"🎯 Initializing evaluation metrics...")
    
    try:
        metrics = [
            # Your Custom Task Span Metric
            BayesianAlignmentMetric(name="bayesian_alignment"),
            
            # Built-in Opik Metrics
            # Note: We use flash-lite to avoid burning through free tier quota too fast
            Hallucination(model="gemini/gemma-3-27b"),
            AnswerRelevance(model="gemini/gemma-3-27b"),
        ]
        
        print(f"✅ Initialized {len(metrics)} metrics")
        
    except Exception as e:
        print(f"❌ Error initializing metrics: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Execute Experiment
    print(f"\n🚀 Starting Experiment: {experiment_name}")
    print(f"🤖 Using Gemini models for evaluation...")
    
    try:
        result = evaluate(
            dataset=dataset,
            task=evaluation_task,
            scoring_metrics=metrics,
            experiment_name=experiment_name,
            task_threads=1,  # Keep at 1 to avoid 429 Rate Limits on free tier
            project_name="skillprotocol-evals"
        )

        print(f"\n{'='*60}")
        print(f"🏆 EXPERIMENT COMPLETED: {experiment_name}")
        print(f"{'='*60}")
        
        # Display results
        if hasattr(result, 'aggregate_scores'):
            print(f"\n📊 AGGREGATE SCORES:")
            for metric_name, score in result.aggregate_scores.items():
                print(f"🔹 {metric_name}: {score:.3f}")
        
        workspace = getattr(settings, 'OPIK_WORKSPACE', 'your-workspace')
        print(f"\n🔗 View detailed results: https://www.comet.com/{workspace}/opik/projects/skillprotocol-evals/experiments")
        
        return result
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())