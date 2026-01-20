"""
Command-line script to run agent optimization
Usage: python run_optimization.py
"""

import asyncio
import sys


async def main():
    from app.optimization.optimize_grader import GraderPromptOptimizer
    
    # Parse arguments
    max_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    model = sys.argv[2] if len(sys.argv) > 2 else "openai/gpt-4o"
    
    print(f"\n⚡ Opik Agent Optimizer for SkillProtocol")
    print(f"Model: {model}")
    print(f"Max Trials: {max_trials}\n")
    
    # Run optimization
    optimizer = GraderPromptOptimizer()
    result = await optimizer.run_optimization(
        max_trials=max_trials,
        model=model
    )
    
    print(f"\n✅ Optimization complete!")
    print(f"📁 Check optimization_results/ for the optimized prompt")


if __name__ == "__main__":
    asyncio.run(main())