# ============================================================================
# FILE: backend/app/evaluation/runner.py
# ============================================================================
"""
Main Evaluation Runner - Executes tests and generates reports with Groq integration
"""

import opik
from opik import Opik, track
from opik.integrations.openai import track_openai
import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from openai import OpenAI

from app.evaluation.golden_dataset import GOLDEN_REPOS, validate_golden_dataset
# CHANGE: Import the classes, not functions
from app.evaluation.metrics import (
    SfiaLevelAccuracy,
    CreditRangeConsistency,
    MarkerDetectionAccuracy,
    ReasoningQuality
)

from app.core.opik_config import OpikManager, PROJECTS, log_evaluation_trace


class SkillProtocolEvaluationRunner:
    """Evaluation runner with Groq integration and correct project routing"""
    
    def __init__(self):
        # Use eval project
        self.client = OpikManager.get_client(PROJECTS["eval"])
        self.project_name = PROJECTS["eval"]

        # Initialize Groq client with OpenAI compatibility
        self.groq_client = OpenAI(
            api_key=os.environ.get("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )
        # Track with Opik for observability
        self.groq_client = track_openai(self.groq_client)

        # CHANGE: Instantiate the metric classes with Groq models
        self.metrics = [
            SfiaLevelAccuracy(model="groq/llama3-70b-8192"),
            CreditRangeConsistency(model="groq/llama3-70b-8192"),
            MarkerDetectionAccuracy(model="groq/llama3-70b-8192"),
            ReasoningQuality(model="groq/llama3-70b-8192")
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
    
    @track(name="Repository Analysis", type="tool")
    async def run_analysis_internal(
        self, 
        repo_url: str, 
        job_id: str, 
        model: str = "groq/llama3-70b-8192"
    ) -> Dict[str, Any]:
        """
        Internal method to run analysis with Groq models
        """
        from app.agents.graph import run_analysis
        
        # Run the analysis with Groq model configuration
        state = await run_analysis(
            repo_url=repo_url,
            user_id="eval_user",
            job_id=job_id,
            llm_client=self.groq_client,  # Pass Groq client
            model=model  # Pass model name
        )
        
        return state
    
    @track(name="Full Evaluation Run", type="tool", project_name="skillprotocol-evals")
    async def run_evaluation(
        self, 
        experiment_name: str = "baseline",
        limit: int = None,
        skip_analysis: bool = False,
        model: str = "groq/llama3-70b-8192"
    ) -> Dict[str, Any]:
        """
        Runs complete evaluation on golden dataset with Groq models
        """
        print(f"\n{'='*80}")
        print(f"🔬 STARTING EVALUATION: {experiment_name} (Powered by Groq)")
        print(f"Model: {model}")
        print(f"{'='*80}\n")
        
        repos_to_eval = GOLDEN_REPOS[:limit] if limit else GOLDEN_REPOS
        results = []
        
        for i, repo_item in enumerate(repos_to_eval):
            repo_name = repo_item["repo_url"].split("/")[-1]
            
            print(f"\n[{i+1}/{len(repos_to_eval)}] Evaluating: {repo_name}")
            print(f"Expected Level: {repo_item['expected_sfia_level']}")
            print(f"Using Model: {model}")
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
                        state = await self.run_analysis_internal(
                            repo_url=repo_item["repo_url"],
                            job_id=f"eval_{experiment_name}_{repo_name}",
                            model=model
                        )
                else:
                    # Run actual analysis with Groq
                    print(f"  🔄 Running analysis with Groq...")
                    state = await self.run_analysis_internal(
                        repo_url=repo_item["repo_url"],
                        job_id=f"eval_{experiment_name}_{repo_name}",
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
                
                # Evaluate with metrics
                metric_scores = {}
                for metric in self.metrics:
                    try:
                        score = await metric.evaluate(
                            predicted=sfia_result,
                            expected=repo_item,
                            context=scan_metrics
                        )
                        metric_scores[metric.name] = score
                        print(f"  ✅ {metric.name}: {score:.3f}")
                    except Exception as e:
                        print(f"  ❌ {metric.name}: Failed - {e}")
                        metric_scores[metric.name] = 0.0
                
                # Store result
                result = {
                    "repo_url": repo_item["repo_url"],
                    "repo_name": repo_name,
                    "expected": repo_item,
                    "predicted": sfia_result,
                    "scan_metrics": scan_metrics,
                    "metric_scores": metric_scores,
                    "model_used": model,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                # Log to Opik with Groq model info
                log_evaluation_trace(
                    repo_url=repo_item["repo_url"],
                    expected=repo_item,
                    predicted=sfia_result,
                    scores=metric_scores,
                    experiment_name=experiment_name,
                    model_info={
                        "provider": "groq",
                        "model": model,
                        "base_url": "https://api.groq.com/openai/v1"
                    }
                )
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                # Log failure
                result = {
                    "repo_url": repo_item["repo_url"],
                    "repo_name": repo_name,
                    "expected": repo_item,
                    "predicted": None,
                    "error": str(e),
                    "model_used": model,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
        
        # Generate summary
        summary = self._generate_summary(results, experiment_name, model)
        
        # Save results
        self._save_results(results, summary, experiment_name)
        
        return {
            "experiment_name": experiment_name,
            "model": model,
            "results": results,
            "summary": summary,
            "total_repos": len(repos_to_eval),
            "successful_evals": len([r for r in results if "error" not in r])
        }
    
    def _generate_summary(self, results: List[Dict], experiment_name: str, model: str) -> Dict[str, Any]:
        """Generate evaluation summary with Groq model info"""
        successful_results = [r for r in results if "error" not in r]
        
        if not successful_results:
            return {
                "experiment_name": experiment_name,
                "model": model,
                "total_repos": len(results),
                "successful_evals": 0,
                "error": "No successful evaluations"
            }
        
        # Calculate average scores per metric
        metric_averages = {}
        for metric in self.metrics:
            scores = [r["metric_scores"].get(metric.name, 0) for r in successful_results]
            metric_averages[metric.name] = {
                "mean": sum(scores) / len(scores) if scores else 0,
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "count": len(scores)
            }
        
        return {
            "experiment_name": experiment_name,
            "model": model,
            "provider": "groq",
            "total_repos": len(results),
            "successful_evals": len(successful_results),
            "failed_evals": len(results) - len(successful_results),
            "metric_averages": metric_averages,
            "timestamp": datetime.now().isoformat()
        }
    
    def _save_results(self, results: List[Dict], summary: Dict, experiment_name: str):
        """Save evaluation results to file"""
        results_dir = Path("evaluation_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = results_dir / f"{experiment_name}_{timestamp}_detailed.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save summary
        summary_file = results_dir / f"{experiment_name}_{timestamp}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Results saved:")
        print(f"  📄 Detailed: {results_file}")
        print(f"  📋 Summary: {summary_file}")

    @track(name="Quick Model Test", type="tool")
    async def test_groq_connection(self, model: str = "groq/llama3-8b-8192") -> bool:
        """Test Groq connection and model availability"""
        try:
            response = self.groq_client.chat.completions.create(
                model=model.replace("groq/", ""),  # Remove prefix for actual API call
                messages=[
                    {"role": "user", "content": "Test connection. Respond with 'OK'."}
                ],
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ Groq connection successful: {result}")
            return True
            
        except Exception as e:
            print(f"❌ Groq connection failed: {e}")
            return False
