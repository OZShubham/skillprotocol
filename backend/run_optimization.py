"""
SkillProtocol - Opik Agent Optimizer (Judge Agent Edition)
NOW FETCHES THE SEED PROMPT FROM THE OPIK LIBRARY.
"""

import os
import sys
import asyncio
import json
import logging
from typing import Any, Dict

import opik
from opik_optimizer import ChatPrompt, MetaPromptOptimizer, OptimizableAgent
from opik.evaluation.metrics import score_result

# App Imports
from app.core.config import settings
from app.core.state import AnalysisState
from app.agents.judge import arbitrate_level

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix for Opik progress bar bug
os.environ["OPIK_DISABLE_PROGRESS_BARS"] = "true"

# --- 1. CONFIGURATION ---
if settings.OPIK_API_KEY:
    os.environ["OPIK_API_KEY"] = settings.OPIK_API_KEY
if settings.OPIK_WORKSPACE:
    os.environ["OPIK_WORKSPACE"] = settings.OPIK_WORKSPACE
if settings.OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY

def get_model_name(model: str) -> str:
    return f"openrouter/{model}" if not model.startswith("openrouter/") else model

OPTIMIZER_MODEL = get_model_name(settings.DEFAULT_MODEL) 
JUDGE_MODEL = get_model_name(settings.JUDGE_MODEL)

# --- 2. CUSTOM AGENT ADAPTER ---
class JudgeOptimizerAgent(OptimizableAgent):
    """
    Connects the Opik Optimizer to the actual SkillProtocol Judge Agent code.
    """
    def invoke_agent(
        self,
        prompts: Dict[str, ChatPrompt],
        dataset_item: Dict[str, Any],
        allow_tool_use: bool = False,
        seed: int | None = None,
    ) -> str:
        # Extract the optimized prompt text
        optimized_prompt_obj = list(prompts.values())[0]
        messages = optimized_prompt_obj.get_messages(dataset_item)
        
        # We assume the prompt template puts the main instructions in the first message
        system_prompt_text = messages[0]["content"]

        # Mock State
        mock_state: AnalysisState = {
            "job_id": f"opt_{os.urandom(4).hex()}",
            "repo_url": dataset_item.get("input", "http://github.com/mock/repo"),
            "user_id": "optimizer_bot",
            "current_step": "judge",
            "progress": 50,
            "scan_metrics": {
                "ncrf": {
                    "total_sloc": dataset_item.get("sloc", 5000),
                    "estimated_learning_hours": dataset_item.get("learning_hours", 100),
                    "ncrf_base_credits": dataset_item.get("credits", 20.0)
                }
            },
            "sfia_result": {
                "sfia_level": int(dataset_item.get("grader_level", 3)), 
                "reasoning": dataset_item.get("grader_reasoning", "Code structure looks solid."),
                "judge_intervened": False
            },
            "validation_result": {
                "bayesian_best_estimate": int(dataset_item.get("bayesian_level", 3)),
                "confidence": float(dataset_item.get("bayesian_confidence", 0.85)),
                "expected_range": [2, 4]
            },
            "semantic_report": {
                "final_witness_statement": dataset_item.get("witness_statement", "Analysis shows consistent patterns."),
                "exhibits": {"Exhibit A": "Clean Architecture detected"}
            },
            # Injecting the prompt override
            "optimizer_override_prompt": system_prompt_text 
        }

        try:
            result_state = asyncio.run(arbitrate_level(mock_state))
            final_level = result_state["sfia_result"].get("sfia_level")
            reasoning = result_state["sfia_result"].get("judge_summary")
            return json.dumps({"final_level": final_level, "reasoning": reasoning})
        except Exception as e:
            return json.dumps({"error": str(e), "final_level": 0})

# --- 3. METRIC ---
def judge_accuracy_metric(dataset_item, llm_output):
    try:
        output_json = json.loads(llm_output)
        predicted_level = int(output_json.get("final_level", 0))
        expected_level = int(dataset_item.get("expected_sfia_level", 0))
        
        if expected_level == 0: return score_result.ScoreResult(name="Accuracy", value=0.0, reason="Invalid Ground Truth")

        if predicted_level == expected_level:
            return score_result.ScoreResult(name="Accuracy", value=1.0, reason="Exact Match")
        elif abs(predicted_level - expected_level) == 1:
            return score_result.ScoreResult(name="Accuracy", value=0.5, reason="Close Call (+/- 1)")
        else:
            return score_result.ScoreResult(name="Accuracy", value=0.0, reason=f"Miss (Pred: {predicted_level}, Exp: {expected_level})")
    except Exception as e:
        return score_result.ScoreResult(name="Accuracy", value=0.0, reason=f"Metric Error: {e}")

def main():
    max_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    print(f"🚀 Starting Judge Optimizer (Budget: {max_trials} trials)")
    
    # 1. Initialize Client
    client = opik.Opik(project_name=settings.OPIK_PROJECT_NAME)

    # 2. Get Dataset
    dataset = client.get_dataset(name="sfia-golden-v1")
    if not dataset:
        print("❌ Dataset not found")
        return
    dataset_items = dataset.get_items()
    print(f"📦 Dataset loaded: {len(dataset_items)} items")

    # --- 3. FETCH PROMPT FROM OPIK LIBRARY ---
    PROMPT_NAME = "judge-agent-rubric"
    print(f"📥 Fetching latest prompt '{PROMPT_NAME}' from Opik Library...")
    
    try:
        # Fetch the Prompt object from the Library
        library_prompt = client.get_prompt(name=PROMPT_NAME)
        
        if not library_prompt:
            raise ValueError(f"Prompt '{PROMPT_NAME}' not found in Opik!")

        # Convert Library Prompt (String/Template) -> Optimizer ChatPrompt
        # We assume your prompt in Opik is stored as the prompt template content.
        current_template = library_prompt.prompt 

        # We construct a ChatPrompt using this fetched template
        initial_prompt = ChatPrompt(
            name=PROMPT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": current_template # <--- Using the fetched content here
                },
                {
                    "role": "user",
                    "content": "Review the evidence and render your verdict."
                }
            ],
            model=JUDGE_MODEL
        )
        print("✅ Successfully loaded seed prompt from Library")

    except Exception as e:
        print(f"❌ Failed to fetch prompt from library: {e}")
        print("💡 Ensure 'judge-agent-rubric' exists in your Opik Prompts Dashboard.")
        return

    # 4. Initialize Optimizer
    optimizer = MetaPromptOptimizer(
        model=OPTIMIZER_MODEL,
        prompts_per_round=2,
        verbose=1
    )

    # 5. Run Optimization
    try:
        result = optimizer.optimize_prompt(
            prompt=initial_prompt,
            agent_class=JudgeOptimizerAgent,
            dataset=dataset,
            metric=judge_accuracy_metric,
            max_trials=max_trials,
            n_samples=5 
        )

        # 6. Output
        print("\n" + "="*60)
        print("🏆 OPTIMIZATION COMPLETE")
        print(f"Original Score: {result.initial_score:.2f}")
        print(f"Best Score:     {result.score:.2f}")
        print("="*60)
        
        print("\n✨ WINNING PROMPT TEMPLATE:")
        print(result.prompt.messages[0]['content'])

        # Save to file
        with open("judge_optimized_prompt.json", "w") as f:
            json.dump({
                "prompt": result.prompt.messages[0]['content'],
                "score": result.score,
                "history": result.history
            }, f, indent=2)
        print("\n💾 Saved to judge_optimized_prompt.json")
        
        # Optional: Push back to Opik as a NEW version or NEW prompt name?
        # client.create_prompt(name="judge-agent-rubric-optimized", prompt=result.prompt.messages[0]['content'])
        
    except Exception as e:
        print(f"❌ Optimization Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()