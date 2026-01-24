# backend/app/optimization/optimize_grader.py
import opik
from opik import Opik
from opik_optimizer import ChatPrompt, MetaPromptOptimizer
import asyncio
import json
from datetime import datetime
from pathlib import Path

# App Imports
from app.evaluation.golden_dataset import GOLDEN_REPOS
# Note: Ensure sfia_level_accuracy is available or define it locally if metrics.py doesn't export it as a standalone function
from app.core.opik_config import OpikManager, PROJECTS
from app.core.config import settings

# Metric function for the optimizer
def grader_metric(dataset_item, llm_output):
    """
    Parses LLM output and checks if the SFIA level matches the expected output.
    """
    try:
        # Handle case where output is a dictionary (parsed JSON) or string
        if isinstance(llm_output, dict):
            pred_level = int(llm_output.get("sfia_level", 0))
        else:
            # Simple string parsing if raw text
            clean_text = llm_output.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            pred_level = int(data.get("sfia_level", 0))

        expected = int(dataset_item["expected_output"]["sfia_level"])
        
        # Binary score: 1.0 if exact match, 0.0 otherwise
        return 1.0 if pred_level == expected else 0.0
    except Exception:
        return 0.0

class GraderPromptOptimizer:
    """Optimizer with correct project routing and LiteLLM support"""
    
    def __init__(self):
        # Use optimizer project defined in opik_config
        self.client = OpikManager.get_client(PROJECTS["optimizer"])
        
        # This is the prompt we want to optimize (from your engine.py)
        self.baseline_prompt_template = """You are a Senior Technical Auditor using SFIA to assess developer capability.

**Repository Statistics:**
- Files: {{input.files_scanned}}
- Total SLOC: {{input.total_sloc}}
- Complexity: {{input.complexity_distribution}}
- Learning Hours: {{input.estimated_learning_hours}}

**Evidence:**
- README: {{input.has_readme}}
- Tests: {{input.has_tests}}
- CI/CD: {{input.has_ci_cd}}
- Docker: {{input.has_docker}}
- Async: {{input.uses_async}}

**Task:** Assign ONE SFIA level (1-5).

**Respond ONLY with valid JSON:**
{
  "sfia_level": 3,
  "reasoning": "explanation",
  "evidence_used": [],
  "confidence": 0.85
}
"""
    
    def prepare_optimization_dataset(self):
        """
        Converts golden repos into format needed by Opik Optimizer
        """
        print("📦 Preparing optimization dataset...")
        
        dataset_items = []
        
        for repo in GOLDEN_REPOS[:10]:  # Use subset for speed
            # Map golden dataset structure to the variables expected by prompt
            item = {
                "input": {
                    "files_scanned": 15, # Placeholder simulation
                    "total_sloc": 1000,
                    "complexity_distribution": "moderate",
                    "estimated_learning_hours": 30,
                    "has_readme": repo.get("markers", {}).get("has_readme", False),
                    "has_tests": repo.get("markers", {}).get("has_tests", False),
                    "has_ci_cd": repo.get("markers", {}).get("has_ci_cd", False),
                    "has_docker": repo.get("markers", {}).get("has_docker", False),
                    "uses_async": repo.get("markers", {}).get("uses_async", False)
                },
                "expected_output": {
                    "sfia_level": str(repo["expected_sfia_level"])
                }
            }
            dataset_items.append(item)
        
        # Create Opik dataset
        dataset_name = "sfia-optimizer-dataset-v1"
        dataset = self.client.get_or_create_dataset(dataset_name)
        dataset.insert(dataset_items)
        
        print(f"✅ Created/Updated dataset '{dataset_name}' with {len(dataset_items)} items")
        return dataset
    
    def run_optimization(self, max_trials: int = 5):
        """
        Runs the optimization using Groq (via LiteLLM conventions)
        """
        # 1. Define Model
        # Using groq/ prefix tells Opik Optimizer to use LiteLLM
        model_name = f"groq/{settings.LLM_MODEL.replace('groq/', '')}"
        
        print(f"🚀 Starting Optimizer using model: {model_name}")
        
        # 2. Prepare Dataset
        dataset = self.prepare_optimization_dataset()
        
        # 3. Initialize Prompt
        # Opik Optimizer expects Mustache syntax {{variable}}
        baseline_prompt = ChatPrompt(
            messages=[{
                "role": "user",
                "content": self.baseline_prompt_template
            }]
        )
        
        # 4. Initialize Optimizer
        optimizer = MetaPromptOptimizer(model=model_name)
        
        # 5. Run
        result = optimizer.optimize_prompt(
            prompt=baseline_prompt,
            dataset=dataset,
            metric=grader_metric,
            max_trials=max_trials,
            verbose=1
        )
        
        print(f"\n🏆 Best Score: {result.best_score}")
        print(f"✨ Optimized Prompt:\n{result.prompt}")
        
        return result

if __name__ == "__main__":
    opt = GraderPromptOptimizer()
    opt.run_optimization(max_trials=3)