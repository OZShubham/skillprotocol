"""
SkillProtocol - SFIA Grader Optimization Script
Run this to scientifically tune the prompt used by the Grader Agent.
"""

import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import opik
from opik.evaluation.metrics import ScoreResult
from opik_optimizer import ChatPrompt, MetaPromptOptimizer

# Load Env
load_dotenv()

# ============================================================================
# 1. DEFINE THE METRIC (The "Judge")
# ============================================================================
def sfia_accuracy_metric(dataset_item, llm_output):
    """
    Determines if the LLM correctly identified the SFIA level based on the markers.
    """
    try:
        # Extract JSON from potential markdown blocks
        clean_output = llm_output.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_output)
        
        predicted_level = int(data.get("sfia_level", 0))
        expected_level = int(dataset_item["expected_level"])
        
        # Calculate score
        diff = abs(predicted_level - expected_level)
        
        if diff == 0:
            return ScoreResult(name="sfia_accuracy", value=1.0, reason="Perfect match")
        elif diff == 1:
            return ScoreResult(name="sfia_accuracy", value=0.5, reason=f"Close. Pred: {predicted_level}, Exp: {expected_level}")
        else:
            return ScoreResult(name="sfia_accuracy", value=0.0, reason=f"Failed. Pred: {predicted_level}, Exp: {expected_level}")
            
    except Exception as e:
        return ScoreResult(name="sfia_accuracy", value=0.0, reason=f"Parse Error: {str(e)}")

# ============================================================================
# 2. DEFINE GOLDEN DATASET (Synthetic Repositories)
# ============================================================================
golden_dataset = [
    {
        "input": "A simple Python script folder.",
        "context_markers": json.dumps({
            "files_scanned": 1, 
            "has_readme": False, 
            "has_tests": False, 
            "has_ci_cd": False
        }),
        "expected_level": 1
    },
    {
        "input": "A collection of scripts with a requirements.txt but no structure.",
        "context_markers": json.dumps({
            "files_scanned": 5, 
            "has_readme": True, 
            "has_requirements": True, 
            "has_modular_structure": False,
            "has_tests": False
        }),
        "expected_level": 2
    },
    {
        "input": "Standard Python package with modular code and README.",
        "context_markers": json.dumps({
            "files_scanned": 15, 
            "has_readme": True, 
            "has_requirements": True, 
            "has_modular_structure": True,
            "has_tests": False
        }),
        "expected_level": 3
    },
    {
        "input": "Professional backend with Unit Tests and OOP patterns.",
        "context_markers": json.dumps({
            "files_scanned": 25, 
            "has_modular_structure": True,
            "has_tests": True, 
            "has_docstrings": True,
            "uses_design_patterns": True,
            "has_ci_cd": False
        }),
        "expected_level": 4
    },
    {
        "input": "Production System with Docker, CI/CD, and Async patterns.",
        "context_markers": json.dumps({
            "files_scanned": 50, 
            "has_tests": True, 
            "has_ci_cd": True, 
            "has_docker": True, 
            "uses_async": True,
            "has_error_handling": True
        }),
        "expected_level": 5
    }
]

# ============================================================================
# 3. RUN OPTIMIZATION
# ============================================================================
def main():
    print("🚀 Starting Opik Agent Optimization for SkillProtocol...")
    
    # 1. Setup Opik
    client = opik.Opik(workspace=os.getenv("OPIK_WORKSPACE"), project="skill-protocol-optimizer")
    
    # 2. Create Dataset
    dataset_name = "sfia-golden-dataset-v1"
    dataset = client.get_or_create_dataset(dataset_name)
    dataset.insert(golden_dataset)
    print(f"✅ Loaded dataset '{dataset_name}' with {len(golden_dataset)} items")

    # 3. Define the Initial Prompt (The one we want to improve)
    # This maps to the prompt in `app/services/scoring/engine.py`
    initial_template = """
    You are an SFIA Auditor. Analyze the following evidence and assign a level (1-5).
    
    Repo Context: {context_markers}
    Description: {input}
    
    Return JSON with 'sfia_level'.
    """
    
    prompt_object = ChatPrompt(
        messages=[{"role": "user", "content": initial_template}],
        model="openai/gpt-4o",  # Optimizer works best with powerful models
    )

    # 4. Initialize MetaPrompt Optimizer
    # This uses a recursive reasoning loop to improve the instructions
    optimizer = MetaPromptOptimizer(model="openai/gpt-4o")

    # 5. Execute Optimization
    print("⏳ Running optimization loop (this may take a minute)...")
    result = optimizer.optimize_prompt(
        prompt=prompt_object,
        dataset=dataset,
        metric=sfia_accuracy_metric,
        max_trials=3,  # Keep low for demo purposes
        verbose=1
    )

    print("\n" + "="*60)
    print("🏆 OPTIMIZATION COMPLETE")
    print("="*60)
    print(f"Original Score: {result.history[0]['score']:.2f}")
    print(f"Final Score:    {result.history[-1]['score']:.2f}")
    print("\n✨ BEST PROMPT FOUND:")
    print(result.prompt)
    print("\n(Copy this prompt back into app/services/scoring/engine.py)")

if __name__ == "__main__":
    main()