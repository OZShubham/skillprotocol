"""
SkillProtocol - SFIA Grader Optimization Script
Uses MetaPromptOptimizer to automatically improve the Grader's system prompt.
"""

import os
import sys
import json
import opik
from opik.evaluation.metrics.score_result import ScoreResult
from opik_optimizer import ChatPrompt, MetaPromptOptimizer
from app.core.config import settings

# Ensure LiteLLM has the API key
if settings.OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY

# ---------------------------------------------------------
# 1. Define Metric
# ---------------------------------------------------------
def sfia_accuracy_metric(dataset_item, llm_output):
    try:
        clean_output = llm_output.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_output)
        predicted = int(data.get("sfia_level", 0))
        
        expected_val = dataset_item.get("expected_sfia_level") or dataset_item.get("expected_output")
        expected = int(expected_val)
        
        diff = abs(predicted - expected)
        if diff == 0: return ScoreResult(name="sfia", value=1.0, reason="Perfect")
        elif diff == 1: return ScoreResult(name="sfia", value=0.5, reason="Close")
        else: return ScoreResult(name="sfia", value=0.0, reason="Miss")
    except:
        return ScoreResult(name="sfia", value=0.0, reason="Parse Error")

# ---------------------------------------------------------
# 2. Main Routine
# ---------------------------------------------------------
def main():
    print("🚀 Starting Opik Optimizer...")

    # Configure Opik
    if not settings.OPIK_API_KEY:
        print("❌ Error: OPIK_API_KEY is missing.")
        return

    opik.configure(
        api_key=settings.OPIK_API_KEY,
        workspace=settings.OPIK_WORKSPACE,
        use_local=False 
    )

    client = opik.Opik(project_name=settings.OPIK_PROJECT_NAME)
    
    # Load Dataset
    try:
        dataset = client.get_dataset(name="sfia-golden-v1")
        if not dataset: raise ValueError("Dataset not found")
        print("📦 Dataset Loaded")
    except:
        print("❌ Dataset missing. Run 'python -m app.scripts.run_feedback_loop' first.")
        return

    # Load Prompt
    PROMPT_NAME = "sfia-grader-v2"
    initial_messages = []
    
    try:
        chat_obj = client.get_chat_prompt(name=PROMPT_NAME)
        if chat_obj:
            print("✅ Loaded Chat Prompt")
            initial_messages = getattr(chat_obj, "messages", None) or getattr(chat_obj, "template", [])
        else:
            prompt_obj = client.get_prompt(name=PROMPT_NAME)
            if prompt_obj:
                print("✅ Loaded Text Prompt")
                initial_messages = [{"role": "user", "content": prompt_obj.prompt}]
            else:
                # Default fallback if prompt doesn't exist yet
                print("⚠️ Prompt not found in library, using default.")
                initial_messages = [{"role": "user", "content": "Analyze {{input}} and return JSON with sfia_level."}]
    except Exception as e:
        print(f"⚠️ Warning: {e}")

    # Initialize Optimizer
    OPTIMIZER_MODEL = "openrouter/google/gemini-2.0-flash-001" 
    
    prompt_object = ChatPrompt(
        messages=initial_messages,
        model=OPTIMIZER_MODEL, 
    )

    optimizer = MetaPromptOptimizer(
        model=OPTIMIZER_MODEL, 
        prompts_per_round=3  # Standard config per docs
    )

    # Run Optimization
    print(f"⏳ Optimizing... (This may take a few minutes)")
    try:
        result = optimizer.optimize_prompt(
            prompt=prompt_object,
            dataset=dataset,
            metric=sfia_accuracy_metric,
            max_trials=10, 
            verbose=0  # ✅ STANDARD FIX: Disable progress bar to avoid tqdm error
        )

        print("\n🏆 OPTIMIZATION COMPLETE")
        print(f"Original Score: {result.history[0]['score']:.2f}")
        print(f"Best Score:     {result.best_score:.2f}")
        
        print("\n✨ BEST PROMPT FOUND:")
        if result.prompt.messages:
            print(result.prompt.messages[0]['content'])
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()