# ============================================================================
# FILE 4: backend/run_evaluation.py (CLI Script)
# ============================================================================
"""
Command-line script to run evaluations
Usage: python run_evaluation.py baseline
"""

import asyncio
import sys
from app.evaluation.runner import SkillProtocolEvaluationRunner


async def main():
    experiment_name = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    runner = SkillProtocolEvaluationRunner()
    
    # Create dataset
    await runner.create_opik_dataset()
    
    # Run evaluation
    results = await runner.run_evaluation(
        experiment_name=experiment_name,
        limit=limit
    )
    
    print(f"\n✅ Evaluation complete!")
    print(f"🔗 View traces: https://www.comet.com/YOUR_WORKSPACE/opik/traces")
    print(f"📁 Results saved to: evaluation_results/{experiment_name}_*.json")


if __name__ == "__main__":
    asyncio.run(main())