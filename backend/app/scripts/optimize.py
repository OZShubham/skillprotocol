from opik_optimizer import ChatPrompt, MetaPromptOptimizer
from opik.evaluation.metrics import AgentTaskCompletionJudge
import opik

client = opik.Opik()

# 1. Define the 'ChatPrompt' object (This is Opik-native)
prompt = ChatPrompt(
    system="You are a Senior SFIA Auditor. Analyze code and assign Level 1-5.",
    user="Analyze this repo: {{repo_url}}" # Must use double braces for Opik
)

# 2. Define the Optimizer
optimizer = MetaPromptOptimizer(
    model="openai/gpt-4o",  # The 'Teacher' model that improves the prompt
    rounds=3                # How many times it tries to rewrite
)

# 3. Define the Metric for the Optimizer
def grader_metric(dataset_item, llm_output):
    judge = AgentTaskCompletionJudge()
    return judge.score(output=llm_output)

if __name__ == "__main__":
    dataset = client.get_dataset(name="sfia-golden-v1")
    
    # This automatically logs a new 'Optimization' run in your dashboard
    result = optimizer.optimize_prompt(
        prompt=prompt,
        dataset=dataset,
        metric=grader_metric
    )
    
    print("🚀 NEW OPTIMIZED PROMPT:")
    print(result.prompt)