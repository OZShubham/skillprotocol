# ============================================================================
# FILE 3: backend/app/evaluation/runner.py
# ============================================================================
"""
Main Evaluation Runner - Executes tests and generates reports
"""

import opik
from opik import Opik, track
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from app.evaluation.golden_dataset import GOLDEN_REPOS, validate_golden_dataset
from app.evaluation.metrics import (
    sfia_level_accuracy,
    credit_range_consistency,
    marker_detection_accuracy,
    reasoning_quality
)

from app.core.opik_config import OpikManager, PROJECTS, log_evaluation_trace


class SkillProtocolEvaluationRunner:
    """Evaluation runner with correct project routing"""
    
    def __init__(self):
        # Use eval project
        self.client = OpikManager.get_client(PROJECTS["eval"])
        self.project_name = PROJECTS["eval"]

        # All metrics to evaluate
        self.metrics = [
            sfia_level_accuracy,
            credit_range_consistency,
            marker_detection_accuracy,
            reasoning_quality
        ]
        
        # Validate dataset on init
        validate_golden_dataset()
    
    async def create_opik_dataset(self):
        """
        Creates the golden dataset in Opik
        """
        print(f"📦 Creating Opik dataset...")
        
        # Create dataset
        dataset = self.client.get_or_create_dataset("sfia-golden-v1")
        
        # Insert data
        dataset.insert(GOLDEN_REPOS)
        
        print(f"✅ Dataset created with {len(GOLDEN_REPOS)} repositories")
        return dataset
    
    @track(name="Full Evaluation Run", type="tool", project="skillprotocol-evals")
    async def run_evaluation(
        self, 
        experiment_name: str = "baseline",
        limit: int = None,
        skip_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        Runs complete evaluation on golden dataset
        
        Args:
            experiment_name: Name for this evaluation run (e.g., "baseline", "optimized")
            limit: Only evaluate first N repos (for testing)
            skip_analysis: If True, load cached results instead of re-running
        
        Returns:
            Complete evaluation results with metrics
        """
        from app.agents.graph import run_analysis
        
        print(f"\n{'='*80}")
        print(f"🔬 STARTING EVALUATION: {experiment_name}")
        print(f"{'='*80}\n")
        
        repos_to_eval = GOLDEN_REPOS[:limit] if limit else GOLDEN_REPOS
        results = []
        
        for i, repo_item in enumerate(repos_to_eval):
            repo_name = repo_item["repo_url"].split("/")[-1]
            
            print(f"\n[{i+1}/{len(repos_to_eval)}] Evaluating: {repo_name}")
            print(f"Expected Level: {repo_item['expected_sfia_level']}")
            print("-" * 60)
            
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
                        state = await run_analysis(
                            repo_url=repo_item["repo_url"],
                            user_id="eval_user",
                            job_id=f"eval_{experiment_name}_{repo_name}"
                        )
                else:
                    # Run actual analysis
                    print(f"  🔄 Running analysis...")
                    state = await run_analysis(
                        repo_url=repo_item["repo_url"],
                        user_id="eval_user",
                        job_id=f"eval_{experiment_name}_{repo_name}"
                    )
                    
                    # Cache results
                    cache_dir = Path("cache")
                    cache_dir.mkdir(exist_ok=True)
                    with open(cache_dir / f"eval_{repo_name}.json", 'w') as f:
                        json.dump(state, f, indent=2)
                
                # Calculate all metrics
                print(f"\n  📊 Calculating metrics...")
                scores = {}
                metric_details = []
                
                for metric in self.metrics:
                    score_result = metric(repo_item, state)
                    scores[score_result.name] = score_result.value
                    metric_details.append(score_result)
                    
                    # Print each metric
                    icon = "✓" if score_result.value >= 0.8 else "~" if score_result.value >= 0.5 else "✗"
                    print(f"  {icon} {score_result.name}: {score_result.value:.1%} - {score_result.reason}")
                
                # Build result object
                result = {
                    "repo_name": repo_name,
                    "repo_url": repo_item["repo_url"],
                    "expected_level": repo_item["expected_sfia_level"],
                    "predicted_level": state.get("sfia_result", {}).get("sfia_level") if state.get("sfia_result") else None,
                    "final_credits": state.get("final_credits", 0),
                    "expected_credits_range": repo_item["expected_credits_range"],
                    **scores,
                    "opik_trace_id": state.get("opik_trace_id"),
                    "errors": state.get("errors", [])
                }
                
                results.append(result)
                
                
                # Log to Opik using the dedicated evaluation logger
                log_evaluation_trace(
                    name=f"Eval: {repo_name}",
                    input_data={
                        "repo_url": repo_item["repo_url"],
                        "expected_level": repo_item["expected_sfia_level"]
                    },
                    output_data=state,
                    metrics=scores 
                )

                # Also log to main client for experiment tracking
                self.client.log_traces({
                    "name": f"Eval: {repo_name}",
                    "tags": [
                        experiment_name, 
                        f"level_{repo_item['expected_sfia_level']}",
                        "evaluation"
                    ],
                    "metadata": {
                        **scores,
                        "experiment": experiment_name
                    }
                })
                
                print(f"  ✅ Logged to Opik")
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                results.append({
                    "repo_name": repo_name,
                    "repo_url": repo_item["repo_url"],
                    "error": str(e),
                    "expected_level": repo_item["expected_sfia_level"]
                })
        
        # Generate summary report
        summary = self._generate_summary(results, experiment_name)
        
        # Save results
        self._save_results(results, summary, experiment_name)
        
        return {
            "experiment": experiment_name,
            "results": results,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_summary(self, results: List[Dict], experiment_name: str) -> Dict[str, Any]:
        """
        Generates aggregate metrics summary
        """
        valid_results = [r for r in results if "error" not in r]
        
        if not valid_results:
            return {
                "error": "No valid results",
                "total_repos": len(results),
                "failed_repos": len(results)
            }
        
        # Calculate averages
        avg_sfia = sum(r.get("sfia_accuracy", 0) for r in valid_results) / len(valid_results)
        avg_credit = sum(r.get("credit_consistency", 0) for r in valid_results) / len(valid_results)
        avg_marker = sum(r.get("marker_accuracy", 0) for r in valid_results) / len(valid_results)
        avg_reasoning = sum(r.get("reasoning_quality", 0) for r in valid_results) / len(valid_results)
        
        overall_score = (avg_sfia + avg_credit + avg_marker + avg_reasoning) / 4
        
        # Level-wise breakdown
        level_accuracy = {}
        for level in range(1, 6):
            level_results = [r for r in valid_results if r["expected_level"] == level]
            if level_results:
                level_acc = sum(r.get("sfia_accuracy", 0) for r in level_results) / len(level_results)
                level_accuracy[f"level_{level}"] = {
                    "accuracy": level_acc,
                    "count": len(level_results)
                }
        
        summary = {
            "experiment": experiment_name,
            "total_repos": len(results),
            "successful": len(valid_results),
            "failed": len(results) - len(valid_results),
            "metrics": {
                "sfia_accuracy": round(avg_sfia, 4),
                "credit_consistency": round(avg_credit, 4),
                "marker_accuracy": round(avg_marker, 4),
                "reasoning_quality": round(avg_reasoning, 4),
                "overall_score": round(overall_score, 4)
            },
            "level_breakdown": level_accuracy
        }
        
        # Print beautiful summary
        print(f"\n{'='*80}")
        print(f"📊 EVALUATION SUMMARY: {experiment_name}")
        print(f"{'='*80}")
        print(f"\nRepositories:")
        print(f"  Total:      {summary['total_repos']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Failed:     {summary['failed']}")
        
        print(f"\nMetrics:")
        print(f"  SFIA Accuracy:        {avg_sfia:.1%}")
        print(f"  Credit Consistency:   {avg_credit:.1%}")
        print(f"  Marker Accuracy:      {avg_marker:.1%}")
        print(f"  Reasoning Quality:    {avg_reasoning:.1%}")
        print(f"\n  📈 OVERALL SCORE:     {overall_score:.1%}")
        
        if level_accuracy:
            print(f"\nLevel-wise Performance:")
            for level in range(1, 6):
                key = f"level_{level}"
                if key in level_accuracy:
                    acc = level_accuracy[key]["accuracy"]
                    count = level_accuracy[key]["count"]
                    print(f"  Level {level}: {acc:.1%} ({count} repos)")
        
        print(f"{'='*80}\n")
        
        return summary
    
    def _save_results(self, results: List[Dict], summary: Dict, experiment_name: str):
        """
        Saves results to JSON file for judges
        """
        output_dir = Path("evaluation_results")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_data = {
            "experiment": experiment_name,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": summary,
            "detailed_results": results
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✅ Results saved to: {output_file}")