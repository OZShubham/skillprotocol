import json
import matplotlib.pyplot as plt

# Load results
with open('evaluation_results/baseline_*.json') as f:
    baseline = json.load(f)

with open('evaluation_results/optimized_*.json') as f:
    optimized = json.load(f)

# Create comparison chart
metrics = ['SFIA Accuracy', 'Credit Consistency', 'Marker Accuracy', 'Overall']

baseline_scores = [
    baseline['summary']['metrics']['sfia_accuracy'],
    baseline['summary']['metrics']['credit_consistency'],
    baseline['summary']['metrics']['marker_accuracy'],
    baseline['summary']['metrics']['overall_score']
]

optimized_scores = [
    optimized['summary']['metrics']['sfia_accuracy'],
    optimized['summary']['metrics']['credit_consistency'],
    optimized['summary']['metrics']['marker_accuracy'],
    optimized['summary']['metrics']['overall_score']
]

x = range(len(metrics))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
bars1 = ax.bar([i - width/2 for i in x], baseline_scores, width, label='Baseline', color='#EF4444')
bars2 = ax.bar([i + width/2 for i in x], optimized_scores, width, label='Optimized', color='#10B981')

ax.set_ylabel('Score')
ax.set_title('SkillProtocol: Opik Agent Optimizer Impact', fontweight='bold', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(metrics)
ax.legend()
ax.set_ylim([0, 1])

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0%}', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('docs/optimizer_impact.png', dpi=300)