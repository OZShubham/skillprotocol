"""
SkillProtocol - SFIA Grader Optimization Script
Fixed for Opik SDK 3.0.1:
1. Adds 'openrouter/' prefix for LiteLLM.
2. Sets OPIK_API_KEY in os.environ to prevent interactive login.
3. Uses dataset.get_items() instead of list(dataset).
4. Updates MetaPromptOptimizer parameters (prompts_per_round).
"""

import os
import json
import opik
from opik.evaluation.metrics import score_result
from opik_optimizer import ChatPrompt, MetaPromptOptimizer
from app.core.config import settings

# Fix for Opik progress bar bug
os.environ["OPIK_DISABLE_PROGRESS_BARS"] = "true"

# --- CRITICAL FIX 1: SILENCE INTERACTIVE PROMPT ---
if settings.OPIK_API_KEY:
    os.environ["OPIK_API_KEY"] = settings.OPIK_API_KEY
    print("🔑 Opik API Key injected into environment.")

if settings.OPIK_WORKSPACE:
    os.environ["OPIK_WORKSPACE"] = settings.OPIK_WORKSPACE
    print(f"🏢 Opik Workspace set to: {settings.OPIK_WORKSPACE}")

# --- CRITICAL FIX 2: LiteLLM Configuration ---
if settings.OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY
    print(f"🔑 LiteLLM configured with OpenRouter Key (ends in ...{settings.OPENROUTER_API_KEY[-4:]})")

# Patch tqdm for Opik compatibility
try:
    import tqdm
    original_tqdm = tqdm.tqdm
    
    def patched_tqdm(iterable=None, *args, **kwargs):
        if iterable is None:
            iterable = []
        return original_tqdm(iterable, *args, **kwargs)
    
    tqdm.tqdm = patched_tqdm
except ImportError:
    pass

# Helper to format model name for LiteLLM
def get_litellm_model_name(model_name: str) -> str:
    if not model_name.startswith("openrouter/"):
        return f"openrouter/{model_name}"
    return model_name

# Use this validated string for all Opik operations
OPTIMIZER_MODEL = get_litellm_model_name(settings.DEFAULT_MODEL)
print(f"🔗 Using Model for Optimization: {OPTIMIZER_MODEL}")


def sfia_accuracy_metric(dataset_item, llm_output):
    """
    Enhanced metric function for SFIA grader evaluation.
    """
    try:
        # Parse LLM output - handle various formats
        if isinstance(llm_output, str):
            clean_output = llm_output.replace("```json", "").replace("```", "").strip()
            
            # Try to extract SFIA level from structured output
            import re
            
            # Look for various level patterns
            level_patterns = [
                r'"sfia_level":\s*(\d+)',
                r'"level":\s*(\d+)',
                r'Level\s*(\d+)',
                r'SFIA\s*Level\s*(\d+)',
                r'assigned_level.*?(\d+)'
            ]
            
            predicted_level = None
            for pattern in level_patterns:
                match = re.search(pattern, clean_output, re.IGNORECASE)
                if match:
                    predicted_level = int(match.group(1))
                    break
            
            if predicted_level is None:
                # Try JSON parsing as fallback
                try:
                    data = json.loads(clean_output)
                    predicted_level = int(data.get("sfia_level") or data.get("level") or 0)
                except:
                    # Last ditch: look for a single digit
                    digit_match = re.search(r'\b[1-5]\b', clean_output)
                    if digit_match:
                        predicted_level = int(digit_match.group(0))
                    else:
                        raise ValueError("Could not extract SFIA level from output")
        else:
            predicted_level = int(llm_output.get("sfia_level") or llm_output.get("level") or 0)

        # Validate SFIA level range
        if not (1 <= predicted_level <= 5):
            return score_result.ScoreResult(
                name="sfia_accuracy", 
                value=0.0, 
                reason=f"Invalid SFIA level: {predicted_level} (must be 1-5)"
            )
        
        # Get expected value from dataset item
        expected_val = (dataset_item.get("expected_sfia_level") or 
                        dataset_item.get("expected_output") or 
                        dataset_item.get("sfia_level"))
        expected_level = int(expected_val) if expected_val is not None else 0

        # Enhanced scoring logic
        diff = abs(predicted_level - expected_level)
        
        if diff == 0:
            return score_result.ScoreResult(
                name="sfia_accuracy", 
                value=1.0, 
                reason=f"Perfect match: Level {predicted_level}"
            )
        elif diff == 1:
            return score_result.ScoreResult(
                name="sfia_accuracy", 
                value=0.6, 
                reason=f"Close match: {predicted_level} vs {expected_level} (±1 level)"
            )
        elif diff == 2:
            return score_result.ScoreResult(
                name="sfia_accuracy", 
                value=0.2, 
                reason=f"Moderate error: {predicted_level} vs {expected_level} (±2 levels)"
            )
        else:
            return score_result.ScoreResult(
                name="sfia_accuracy", 
                value=0.0, 
                reason=f"Major error: {predicted_level} vs {expected_level} (±{diff} levels)"
            )

    except Exception as e:
        return score_result.ScoreResult(
            name="sfia_accuracy", 
            value=0.0, 
            reason=f"Parse Error: {str(e)}"
        )

def main():
    print("🚀 Starting SFIA Grader Optimization...")

    try:
        # 1. Initialize Opik Client
        client = opik.Opik(
            project_name=settings.OPIK_PROJECT_NAME,
            # Keys are picked up from os.environ injected above
        )

        # 2. Load Dataset
        DATASET_NAME = "sfia-golden-v1"
        print(f"📦 Loading dataset: {DATASET_NAME}")
        
        dataset = client.get_dataset(name=DATASET_NAME)
        if not dataset:
            print(f"❌ Dataset '{DATASET_NAME}' not found. Please create it first.")
            return
        
        # --- CRITICAL FIX 3: Use .get_items() instead of list() ---
        try:
            # SDK 3.0+ uses get_content() or items attribute, handling both versions carefully
            if hasattr(dataset, "get_content"):
                dataset_items = dataset.get_content()
            elif hasattr(dataset, "get_items"):
                dataset_items = dataset.get_items()
            else:
                # Fallback for some SDK versions
                dataset_items = list(dataset)
        except TypeError:
             # If list() failed earlier, it means it's not iterable, try to proceed without counting
             print("⚠️  Could not count dataset items eagerly, proceeding...")
             dataset_items = []

        print(f"✅ Dataset loaded")

        # 3. Create baseline prompt
        baseline_prompt = ChatPrompt(
            name="sfia-grader-optimization-baseline",
            messages=[
                {
                    "role": "system",
                    "content": """You are an Elite SFIA Assessment Specialist.

**🎯 MISSION:** Accurately assess SFIA level (1-5) using pre-analyzed data.

**📊 REPOSITORY ANALYSIS DATA:**

**Quantitative Metrics:**
- SLOC: {sloc}
- Complexity: {complexity}
- Complexity Density: {complexity_density}
- Maintainability Index: {avg_mi}/100
- Language: {dominant_language}
- Files Analyzed: {files_scanned}

**Architectural Analysis:**
- Design Patterns Found: {patterns_found}
- Sophistication Level: {sophistication}
- Architectural Maturity: {architectural_maturity}/10
- Quality Level: {quality_level}

**Detected Markers:**
- README: {has_readme}
- Tests: {has_tests}
- CI/CD: {has_ci_cd}
- Docker: {has_docker}
- Error Handling: {has_error_handling}
- Async Patterns: {uses_async}
- Modular Structure: {has_modular_structure}

**🔮 STATISTICAL ANCHOR:**
- Bayesian Model Estimate: Level {bayesian_level} ({bayesian_confidence} confidence)

**🧠 ASSESSMENT WORKFLOW:**

1. **Form Initial Hypothesis** based on the metrics above
2. **Validate Against Evidence** - consider all quantitative and qualitative indicators
3. **Make Final Decision** - provide SFIA level (1-5) with clear reasoning

**⚠️ CRITICAL RULES:**
1. Trust the pre-analyzed data - it's comprehensive
2. Cite specific evidence from the metrics
3. Align with Bayesian prior unless strong contrary evidence exists
4. Provide level as integer 1-5

**Response Format:**
```json
{
  "sfia_level": <integer 1-5>,
  "reasoning": "<detailed explanation citing specific metrics>",
  "confidence": "<high/medium/low>",
  "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
}
```"""
                },
                {
                    "role": "user",
                    "content": "Please analyze this repository and provide your SFIA assessment using the data provided above."
                }
            ],
            model=OPTIMIZER_MODEL 
        )

        print("✅ Baseline prompt created")

        # 4. Initialize MetaPrompt Optimizer (SDK 3.0.1 Compatible)
        # --- CRITICAL FIX 4: Updated parameter names ---
        optimizer = MetaPromptOptimizer(
            model=OPTIMIZER_MODEL,
            prompts_per_round=2,  # CHANGED: 'candidates_per_round' -> 'prompts_per_round'
            # REMOVED: max_iterations=3 (This is now max_trials in optimize_prompt)
            verbose=0,
            seed=42
        )

        print("✅ Optimizer initialized")

        # 5. Run Optimization
        print("⏳ Starting optimization process...")
        print(f"Using model: {OPTIMIZER_MODEL}")
        
        # Use smaller sample for testing if dataset items are available
        sample_size = min(20, len(dataset_items)) if dataset_items else 10
        print(f"Using {sample_size} samples for optimization")
        
        result = optimizer.optimize_prompt(
            prompt=baseline_prompt,
            dataset=dataset,
            metric=sfia_accuracy_metric,
            max_trials=5, # Controls total iterations now
            project_name=settings.OPIK_PROJECT_NAME,
            n_samples=sample_size
        )

        # 6. Display Results
        print("\n" + "="*70)
        print("🏆 SFIA GRADER OPTIMIZATION COMPLETE")
        print("="*70)
        print(f"📊 Original Score:    {result.initial_score:.4f}")
        print(f"🎯 Final Score:       {result.score:.4f}")
        print(f"📈 Improvement:       {result.score - result.initial_score:.4f}")
        # Note: optimizer name might not be available in result object in 3.0.1
        # print(f"🤖 Optimizer Used:    {result.optimizer}") 
        # print(f"💬 LLM Calls Made:    {result.llm_calls}")
        # print(f"💰 Total Cost:        ${result.llm_cost_total:.4f}")

        # Display optimized prompt
        print("\n" + "-" * 50)
        print("✨ OPTIMIZED PROMPT (Preview):")
        print("-" * 50)
        
        best_prompt = result.prompt
        system_content = best_prompt.messages[0]['content']
        preview = system_content[:500] + "..." if len(system_content) > 500 else system_content
        print(preview)

        # 7. Save Results
        output_file = "sfia_optimization_results.json"
        
        results_data = {
            "optimization_metadata": {
                "dataset_name": DATASET_NAME,
                "model_used": OPTIMIZER_MODEL,
                "optimization_date": "2024-01-15"
            },
            "performance_metrics": {
                "initial_score": result.initial_score,
                "final_score": result.score,
                "improvement": result.score - result.initial_score,
            },
            "optimized_prompt": {
                "name": best_prompt.name,
                "messages": best_prompt.messages,
                "model": best_prompt.model
            }
        }

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}")
        print("🎉 Optimization completed successfully!")

    except Exception as e:
        print(f"❌ Error during optimization: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()