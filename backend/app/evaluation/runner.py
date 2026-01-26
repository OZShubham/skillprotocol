# ============================================================================
# FILE: backend/app/evaluation/runner.py
# ============================================================================
"""
Main Evaluation Runner - Executes tests and generates reports with Gemini integration
"""

import opik
from opik import Opik, track
from opik.evaluation import evaluate
import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# CHANGE: Import the classes, not functions
from app.evaluation.metrics import (
    SfiaLevelAccuracy,
    CreditRangeConsistency,
    MarkerDetectionAccuracy,
    ReasoningQuality
)

from app.core.opik_config import OpikManager, PROJECTS, log_evaluation_trace


class SkillProtocolEvaluationRunner:
    """Evaluation runner with Gemini integration and Opik's evaluation framework"""
    
    def __init__(self):
        # Use eval project
        self.client = OpikManager.get_client(PROJECTS["eval"])
        self.project_name = PROJECTS["eval"]

        # Set up Gemini API key
        if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
            raise ValueError("Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")

        # CHANGE: Update metrics to use Gemini models
        self.metrics = [
            SfiaLevelAccuracy(model="gemini/gemma-3-27b"),
            CreditRangeConsistency(model="gemini/gemma-3-27b"),
            MarkerDetectionAccuracy(model="gemini/gemma-3-27b"),
            ReasoningQuality(model="gemini/gemma-3-27b")
        ]
        
        # Load dataset from Opik
        self.dataset = self.load_opik_dataset()
    
    def load_opik_dataset(self):
        """
        Load the golden dataset from Opik
        """
        print(f"📦 Loading dataset 'sfia-golden-v1' from Opik...")
        
        try:
            # Get the existing dataset from Opik
            dataset = self.client.get_dataset(name="sfia-golden-v1")
            
            # Get count of items for logging
            dataset_items = list(dataset.get_items())
            print(f"✅ Dataset loaded with {len(dataset_items)} repositories")
            
            return dataset
            
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            print("💡 Make sure the dataset 'sfia-golden-v1' exists in your Opik workspace")
            raise
    
    @track(name="Repository Analysis", type="tool")
    async def run_analysis_internal(
        self, 
        repo_url: str, 
        job_id: str, 
        model: str = "gemini/gemini-2.0-flash-lite"
    ) -> Dict[str, Any]:
        """
        Internal method to run analysis with Gemini models
        """
        from app.agents.graph import run_analysis
        
        # Call run_analysis with only the parameters it expects
        state = await run_analysis(
            repo_url=repo_url,
            user_id="eval_user",
            job_id=job_id,
            user_github_token=None  # Optional parameter
        )
        
        return state
    
    def create_evaluation_task(self, model: str = "gemini/gemini-2.0-flash", skip_analysis: bool = False):
        """
        Create the evaluation task function for Opik's evaluate framework
        """
        async def evaluation_task(dataset_item: Dict[str, Any]) -> Dict[str, Any]:
            """
            Evaluation task that processes each dataset item
            
            Args:
                dataset_item: Dictionary with 'input' (repo_url) and 'expected_output' (sfia_level)
            
            Returns:
                Dictionary with analysis results
            """
            repo_url = dataset_item["input"]
            expected_sfia_level = int(dataset_item["expected_output"])
            repo_name = repo_url.split("/")[-1]
            
            print(f"🔄 Evaluating: {repo_name} (Expected Level: {expected_sfia_level})")
            
            try:
                if skip_analysis:
                    # Load from cache (for faster iteration)
                    cache_file = Path(f"cache/eval_{repo_name}.json")
                    if cache_file.exists():
                        with open(cache_file, 'r') as f:
                            state = json.load(f)
                        print(f"  📁 Loaded from cache")
                    else:
                        print(f"  ⚠️  No cache found, running analysis...")
                        state = await self.run_analysis_internal(
                            repo_url=repo_url,
                            job_id=f"eval_{repo_name}",
                            model=model
                        )
                else:
                    # Run actual analysis with Gemini
                    print(f"  🔄 Running analysis with Gemini...")
                    state = await self.run_analysis_internal(
                        repo_url=repo_url,
                        job_id=f"eval_{repo_name}",
                        model=model
                    )
                    
                    # Cache results
                    cache_dir = Path("cache")
                    cache_dir.mkdir(exist_ok=True)
                    cache_file = cache_dir / f"eval_{repo_name}.json"
                    with open(cache_file, 'w') as f:
                        json.dump(state, f, indent=2)
                
                # Extract results for evaluation
                sfia_result = state.get("sfia_result", {})
                scan_metrics = state.get("scan_metrics", {})
                
                # Return structured result for Opik evaluation
                return {
                    "repo_url": repo_url,
                    "repo_name": repo_name,
                    "expected_sfia_level": expected_sfia_level,
                    "predicted_sfia_result": sfia_result,
                    "scan_metrics": scan_metrics,
                    "analysis_state": state
                }
                
            except Exception as e:
                print(f"  ❌ Error evaluating {repo_name}: {e}")
                return {
                    "repo_url": repo_url,
                    "repo_name": repo_name,
                    "expected_sfia_level": expected_sfia_level,
                    "predicted_sfia_result": None,
                    "scan_metrics": None,
                    "analysis_state": None,
                    "error": str(e)
                }
        
        return evaluation_task
    
    @track(name="Full Evaluation Run", type="tool", project_name="skillprotocol-evals")
    async def run_evaluation(
        self, 
        experiment_name: str = "baseline",
        limit: Optional[int] = None,
        skip_analysis: bool = False,
        model: str = "gemini/gemini-2.0-flash"
    ) -> Dict[str, Any]:
        """
        Runs complete evaluation on golden dataset using Opik's evaluation framework
        """
        print(f"\n{'='*80}")
        print(f"🔬 STARTING EVALUATION: {experiment_name} (Powered by Gemini)")
        print(f"Model: {model}")
        print(f"Dataset: sfia-golden-v1")
        if limit:
            print(f"Limit: {limit} repositories")
        print(f"{'='*80}\n")
        
        try:
            # Create the evaluation task
            evaluation_task = self.create_evaluation_task(model=model, skip_analysis=skip_analysis)
            
            # Prepare dataset for evaluation
            dataset_to_use = self.dataset
            if limit:
                # If limit is specified, we need to create a subset
                all_items = list(self.dataset.get_items())
                limited_items = all_items[:limit]
                
                # Create a temporary dataset with limited items
                temp_dataset_name = f"sfia-golden-v1-limited-{limit}"
                temp_dataset = self.client.get_or_create_dataset(name=temp_dataset_name)
                
                # Clear and insert limited items
                temp_dataset.insert([
                    {"input": item["input"], "expected_output": item["expected_output"]} 
                    for item in limited_items
                ])
                dataset_to_use = temp_dataset
            
            # Run evaluation using Opik's framework
            print(f"🚀 Starting Opik evaluation...")
            evaluation_result = await evaluate(
                dataset=dataset_to_use,
                task=evaluation_task,
                scoring_metrics=self.metrics,
                experiment_name=f"{experiment_name}-gemini",
                project_name=self.project_name
            )
            
            print(f"\n{'='*80}")
            print(f"✅ EVALUATION COMPLETED: {experiment_name}")
            print(f"{'='*80}")
            
            # Extract and display summary metrics
            if hasattr(evaluation_result, 'aggregate_scores'):
                print(f"\n📊 SUMMARY METRICS:")
                for metric_name, score in evaluation_result.aggregate_scores.items():
                    print(f"  {metric_name}: {score:.3f}")
            
            # Return comprehensive results
            return {
                "experiment_name": experiment_name,
                "model": model,
                "dataset_name": "sfia-golden-v1",
                "evaluation_result": evaluation_result,
                "timestamp": datetime.now().isoformat(),
                "total_items_evaluated": limit or len(list(self.dataset.get_items())),
                "skip_analysis": skip_analysis
            }
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            raise
    
    @track(name="Quick Evaluation", type="tool", project_name="skillprotocol-evals")
    async def run_quick_evaluation(
        self,
        experiment_name: str = "quick-test",
        sample_size: int = 5,
        model: str = "gemini/gemini-2.0-flash"
    ) -> Dict[str, Any]:
        """
        Run a quick evaluation on a small sample for testing
        """
        print(f"🚀 Running quick evaluation with {sample_size} samples...")
        
        return await self.run_evaluation(
            experiment_name=experiment_name,
            limit=sample_size,
            skip_analysis=False,
            model=model
        )
    
    @track(name="Cached Evaluation", type="tool", project_name="skillprotocol-evals")
    async def run_cached_evaluation(
        self,
        experiment_name: str = "cached-test",
        limit: Optional[int] = None,
        model: str = "gemini/gemini-2.0-flash"
    ) -> Dict[str, Any]:
        """
        Run evaluation using cached analysis results for faster iteration
        """
        print(f"📁 Running cached evaluation...")
        
        return await self.run_evaluation(
            experiment_name=experiment_name,
            limit=limit,
            skip_analysis=True,
            model=model
        )
    
    def get_evaluation_summary(self, evaluation_result) -> Dict[str, Any]:
        """
        Extract and format evaluation summary from Opik results
        """
        summary = {
            "total_evaluated": 0,
            "successful_evaluations": 0,
            "failed_evaluations": 0,
            "average_scores": {},
            "score_distribution": {}
        }
        
        if hasattr(evaluation_result, 'aggregate_scores'):
            summary["average_scores"] = evaluation_result.aggregate_scores
        
        if hasattr(evaluation_result, 'experiment_items'):
            summary["total_evaluated"] = len(evaluation_result.experiment_items)
            # Add more detailed analysis here if needed
        
        return summary


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def main():
    """Example usage of the evaluation runner"""
    
    runner = SkillProtocolEvaluationRunner()
    
    # Quick test with 3 repositories
    print("Running quick evaluation...")
    quick_result = await runner.run_quick_evaluation(
        experiment_name="gemini-quick-test",
        sample_size=3,
        model="gemini/gemini-2.0-flash"
    )
    
    # Full evaluation
    print("\nRunning full evaluation...")
    full_result = await runner.run_evaluation(
        experiment_name="gemini-full-eval",
        model="gemini/gemini-2.0-flash"
    )
    
    # Cached evaluation for faster iteration
    print("\nRunning cached evaluation...")
    cached_result = await runner.run_cached_evaluation(
        experiment_name="gemini-cached-eval",
        limit=10,
        model="gemini/gemini-2.0-flash"
    )
    
    return {
        "quick": quick_result,
        "full": full_result,
        "cached": cached_result
    }


if __name__ == "__main__":
    # Run the evaluation
    results = asyncio.run(main())
    print("\n🎉 All evaluations completed!")
