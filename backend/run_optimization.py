"""
SkillProtocol - Opik Agent Optimizer with Groq
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
    client = opik.Opik(project_name=settings.OPIK_PROJECT_NAME)
    
    # Set your Groq API key
    os.environ["GROQ_API_KEY"] = "your-groq-api-key"
    
    # 1. Define the current "Draft" Prompt
    prompt = ChatPrompt(
        system="""You are a Senior SFIA Auditor. 
        Analyze the provided codebase metrics and assign an SFIA level (1-5).""",
        user="Repo Metrics: {{context}}"
    )

    # 2. Define the Metric (The 'Teacher' model)
    def optimization_metric(dataset_item, llm_output):
        judge = AgentTaskCompletionJudge()
        payload = f"TASK: Correctly identify SFIA Level {dataset_item['expected_sfia_level']}. AGENT DECISION: {llm_output}"
        return judge.score(output=payload)

    # 3. Initialize Meta-Prompt Optimizer with Groq
    print(f"🧠 Initializing Optimizer (Rounds: {rounds})...")
    optimizer = MetaPromptOptimizer(
        model="groq/llama3-70b-8192",          # Groq model via LiteLLM
        reasoning_model="groq/llama3-70b-8192", # Can use different model for reasoning
        rounds=rounds
    )

    # 4. Run the Optimization Loop
    dataset = client.get_dataset(name="sfia-golden-v1")
    result = optimizer.optimize_prompt(
        prompt=prompt,
        dataset=dataset,
        metric=optimization_metric,
        n_samples=10
    )

    # 5. Display & Save
    print("\n" + "="*60)
    print("🏆 OPTIMIZATION COMPLETE")
    print(f"Original Score: {result.history[0]['score']:.2f}")
    print(f"Final Best Score: {result.best_score:.2f}")
    print("="*60)
    
    print("\n✨ WINNING PROMPT (Update this in Opik UI):")
    print(result.prompt)
    
    result.display()

if __name__ == "__main__":
    main()
