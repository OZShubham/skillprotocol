"""
SkillProtocol - Opik Agent Optimizer
Usage: python run_optimization.py [rounds]
"""
import os
import sys
import opik
from opik_optimizer import ChatPrompt, MetaPromptOptimizer
from opik.evaluation.metrics import AgentTaskCompletionJudge

# App Imports
from app.core.config import settings

def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    
    # 1. Initialize Opik Client
    client = opik.Opik(
        project_name=settings.OPIK_PROJECT_NAME,
        api_key=settings.OPIK_API_KEY,
        workspace=settings.OPIK_WORKSPACE
    )
    
    # 2. Configure LiteLLM for OpenRouter
    # Opik Optimizer uses LiteLLM internally. We must set the API key in os.environ.
    if settings.OPENROUTER_API_KEY:
        os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY
    
    # 3. Define the 'Teacher' Model (The Optimizer)
    # We use the prefix 'openrouter/' so LiteLLM knows where to send the request.
    # Using Llama 3.3 70B as the optimizer is cost-effective and smart.
    OPTIMIZER_MODEL = "openrouter/meta-llama/llama-3.3-70b-instruct"
    
    # 4. Define the current "Draft" Prompt
    # This uses Mustache syntax {{variable}}
    prompt = ChatPrompt(
        system="""You are a Senior SFIA Auditor. 
        Analyze the provided codebase metrics and assign an SFIA level (1-5).""",
        user="Repo Metrics: {{context}}",
        model=OPTIMIZER_MODEL  # Associate the model with the prompt
    )

    # 5. Define the Metric (The 'Judge')
    # This checks if the Agent's output matches the expected output in the dataset.
    def optimization_metric(dataset_item, llm_output):
        judge = AgentTaskCompletionJudge(
            model=OPTIMIZER_MODEL # Use the same OpenRouter model for judging
        )
        payload = f"TASK: Correctly identify SFIA Level {dataset_item['expected_sfia_level']}. AGENT DECISION: {llm_output}"
        return judge.score(output=payload)

    # 6. Initialize Meta-Prompt Optimizer
    print(f"🧠 Initializing Optimizer (Rounds: {rounds})...")
    print(f"🔗 Using Model: {OPTIMIZER_MODEL}")
    
    optimizer = MetaPromptOptimizer(
        model=OPTIMIZER_MODEL,          # The model that rewrites the prompts
        reasoning_model=OPTIMIZER_MODEL, # The model used for intermediate reasoning steps
        rounds=rounds
    )

    # 7. Run the Optimization Loop
    print("📦 Fetching Dataset 'sfia-golden-v1'...")
    try:
        dataset = client.get_dataset(name="sfia-golden-v1")
        if not dataset:
            raise ValueError("Dataset is empty or does not exist.")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        print("💡 Tip: Run 'python -m app.scripts.run_feedback_loop' to create the dataset first.")
        return

    result = optimizer.optimize_prompt(
        prompt=prompt,
        dataset=dataset,
        metric=optimization_metric,
        n_samples=10 # Uses 10 random samples from dataset per round
    )

    # 8. Display & Save
    print("\n" + "="*60)
    print("🏆 OPTIMIZATION COMPLETE")
    print(f"Original Score: {result.history[0]['score']:.2f}")
    print(f"Final Best Score: {result.best_score:.2f}")
    print("="*60)
    
    print("\n✨ WINNING PROMPT (Update this in Opik UI):")
    print(result.prompt)
    
    # Optional: Automatically push the winning prompt back to the library?
    # client.create_prompt(name="sfia-grader-v2", prompt=result.prompt)

if __name__ == "__main__":
    main()