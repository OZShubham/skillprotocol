# ============================================================================
# FILE 5: backend/app/optimization/optimize_grader.py
# ============================================================================
"""
Opik Agent Optimizer - THE HACKATHON SECRET WEAPON
This automatically improves your SFIA grading prompt using meta-prompting
"""

import opik
from opik import Opik
from opik_optimizer import ChatPrompt, MetaPromptOptimizer
import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.evaluation.golden_dataset import GOLDEN_REPOS
from app.evaluation.metrics import sfia_level_accuracy


from app.core.opik_config import OpikManager, PROJECTS


class GraderPromptOptimizer:
    """Optimizer with correct project routing"""
    
    def __init__(self):
        # Use optimizer project
        self.client = OpikManager.get_client(PROJECTS["optimizer"])
        
        # Current prompt from your engine.py
        self.baseline_prompt_template = """You are a Senior Technical Auditor using SFIA (Skills Framework for the Information Age) to assess developer capability.

**Repository Statistics:**
- Files: {files_scanned}
- Total SLOC: {total_sloc}
- Complexity: {complexity_distribution}
- Learning Hours: {estimated_learning_hours}

**Evidence Detected:**
✓ README: {has_readme}
✓ Dependencies defined: {has_requirements}
✓ Modular (3+ files): {has_modular_structure}
✓ Tests: {has_tests}
✓ Docstrings: {has_docstrings}
✓ Design Patterns (OOP): {uses_design_patterns}
✓ CI/CD: {has_ci_cd}
✓ Docker: {has_docker}
✓ Error Handling: {has_error_handling}
✓ Async/Advanced: {uses_async}

**SFIA Levels (GitHub-Provable):**
Level 1 - Follow: Single-file scripts, no structure, basic syntax only.
Level 2 - Assist: Multiple files with functions, but missing README/requirements. Needs guidance.
Level 3 - Apply: ✓README + ✓Requirements + ✓Modular. Professional baseline. Works independently.
Level 4 - Enable: ✓Level 3 + ✓Tests + ✓Docstrings + OOP. Can mentor juniors. Complex problem-solving.
Level 5 - Ensure: ✓Level 4 + ✓CI/CD + ✓Docker + Production patterns. Owns system reliability.

NOTE: Levels 6-7 require organizational impact evidence (not provable from code alone).

**Task:** Assign ONE level (1-5) based on EVIDENCE, not potential. Be conservative.

**Respond ONLY with valid JSON:**
{{
  "sfia_level": 3,
  "reasoning": "Clear explanation linking evidence to level",
  "evidence_used": ["README present", "No tests found"],
  "missing_for_next_level": ["Unit tests required for L4"],
  "confidence": 0.85
}}
"""
    
    async def prepare_optimization_dataset(self):
        """
        Converts golden repos into format needed by Opik Optimizer
        """
        print("📦 Preparing optimization dataset...")
        
        dataset_items = []
        
        for repo in GOLDEN_REPOS[:10]:  # Use subset for faster optimization
            # Simulate the data that would be passed to the prompt
            item = {
                "input": {
                    "files_scanned": 15,  # Placeholder - in real eval this comes from scan
                    "total_sloc": 1000,
                    "complexity_distribution": {"moderate": 800, "complex": 200},
                    "estimated_learning_hours": 30,
                    "has_readme": repo.get("markers", {}).get("has_readme", False),
                    "has_requirements": repo.get("markers", {}).get("has_requirements", False),
                    "has_modular_structure": True,
                    "has_tests": repo.get("markers", {}).get("has_tests", False),
                    "has_docstrings": False,
                    "uses_design_patterns": False,
                    "has_ci_cd": repo.get("markers", {}).get("has_ci_cd", False),
                    "has_docker": repo.get("markers", {}).get("has_docker", False),
                    "has_error_handling": False,
                    "uses_async": repo.get("markers", {}).get("uses_async", False)
                },
                "expected_output": {
                    "sfia_level": repo["expected_sfia_level"]
                },
                "metadata": {
                    "repo_url": repo["repo_url"],
                    "reasoning": repo["reasoning"]
                }
            }
            
            dataset_items.append(item)
        
        # Create Opik dataset
        dataset = self.client.get_or_create_dataset("sfia-optimizer-dataset-v1")
        dataset.insert(dataset_items)
        
        print(f"✅ Created optimizer dataset with {len(dataset_items)} items")
        return dataset
    
    async def run_optimization(
        self, 
        max_trials: int = 5,
        model: str = "openai/gpt-4o"
    ):
        """
        Runs the optimization loop
        
        Args:
            max_trials: Number of optimization iterations (more = better but slower)
            model: Model to use for optimization (gpt-4o recommended)
        """
        print(f"\n{'='*80}")
        print(f"🚀 STARTING AGENT OPTIMIZER")
        print(f"{'='*80}\n")
        print(f"Model: {model}")
        print(f"Max Trials: {max_trials}")
        print(f"This will take ~{max_trials * 2} minutes...")
        print()
        
        # Prepare dataset
        dataset = await self.prepare_optimization_dataset()
        
        # Create baseline prompt object
        baseline_prompt = ChatPrompt(
            messages=[{
                "role": "user",
                "content": self.baseline_prompt_template
            }],
            model=model
        )
        
        # Initialize optimizer
        print("🧠 Initializing Meta-Prompt Optimizer...")
        optimizer = MetaPromptOptimizer(model=model)
        
        # Run optimization
        print("⏳ Running optimization loop...\n")
        
        result = optimizer.optimize_prompt(
            prompt=baseline_prompt,
            dataset=dataset,
            metric=sfia_level_accuracy,
            max_trials=max_trials,
            verbose=1  # Show progress
        )
        
        # Print results
        print(f"\n{'='*80}")
        print(f"🏆 OPTIMIZATION COMPLETE")
        print(f"{'='*80}\n")
        
        baseline_score = result.history[0]['score']
        final_score = result.history[-1]['score']
        improvement = final_score - baseline_score
        
        print(f"📊 Results:")
        print(f"  Baseline Accuracy:   {baseline_score:.1%}")
        print(f"  Optimized Accuracy:  {final_score:.1%}")
        print(f"  Improvement:         {improvement:+.1%}")
        print()
        
        # Show iteration history
        print(f"📈 Optimization History:")
        for i, trial in enumerate(result.history):
            print(f"  Trial {i+1}: {trial['score']:.1%}")
        print()
        
        # Save optimized prompt
        self._save_optimized_prompt(result.prompt, baseline_score, final_score)
        
        # Generate comparison report
        self._generate_comparison_report(result.history)
        
        return result
    
    def _save_optimized_prompt(self, optimized_prompt, baseline_score, final_score):
        """
        Saves the optimized prompt to a file
        """
        output_dir = Path("optimization_results")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"optimized_prompt_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("OPTIMIZED SFIA GRADING PROMPT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Baseline Accuracy: {baseline_score:.1%}\n")
            f.write(f"Optimized Accuracy: {final_score:.1%}\n")
            f.write(f"Improvement: {(final_score - baseline_score):+.1%}\n\n")
            f.write("="*80 + "\n\n")
            f.write(str(optimized_prompt))
            f.write("\n\n")
            f.write("="*80 + "\n")
            f.write("INSTRUCTIONS FOR USE:\n")
            f.write("="*80 + "\n")
            f.write("1. Copy the prompt content above\n")
            f.write("2. Replace the prompt in app/services/scoring/engine.py\n")
            f.write("3. Specifically update the get_sfia_rubric_prompt() method\n")
            f.write("4. Re-run evaluation to verify improvement\n")
        
        print(f"✅ Optimized prompt saved to: {output_file}")
        print(f"\n📋 Next Steps:")
        print(f"   1. Review the optimized prompt in: {output_file}")
        print(f"   2. Copy it to app/services/scoring/engine.py")
        print(f"   3. Run: python run_evaluation.py optimized")
    
    def _generate_comparison_report(self, history):
        """
        Generates a visual comparison chart
        """
        try:
            import matplotlib.pyplot as plt
            
            trials = list(range(1, len(history) + 1))
            scores = [h['score'] for h in history]
            
            plt.figure(figsize=(10, 6))
            plt.plot(trials, scores, marker='o', linewidth=2, markersize=8)
            plt.axhline(y=scores[0], color='r', linestyle='--', label='Baseline')
            plt.axhline(y=scores[-1], color='g', linestyle='--', label='Optimized')
            
            plt.xlabel('Optimization Trial', fontsize=12)
            plt.ylabel('SFIA Accuracy Score', fontsize=12)
            plt.title('Opik Agent Optimizer - Performance Improvement', fontsize=14, fontweight='bold')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Add improvement annotation
            improvement = scores[-1] - scores[0]
            plt.text(
                len(trials) / 2, 
                max(scores) * 0.95, 
                f'Improvement: {improvement:+.1%}',
                ha='center',
                fontsize=12,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
            
            output_file = Path("optimization_results") / "optimization_chart.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            
            print(f"✅ Comparison chart saved to: {output_file}")
            
        except ImportError:
            print("⚠️  matplotlib not installed, skipping chart generation")
