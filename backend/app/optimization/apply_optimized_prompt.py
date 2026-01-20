# ============================================================================
# FILE 7: backend/app/optimization/apply_optimized_prompt.py
# ============================================================================
"""
Helper script to apply optimized prompt back to engine.py
"""

import re
from pathlib import Path


def apply_optimized_prompt(optimized_prompt_file: str):
    """
    Automatically updates engine.py with the optimized prompt
    """
    # Read optimized prompt
    with open(optimized_prompt_file, 'r') as f:
        content = f.read()
    
    # Extract just the prompt content (remove metadata)
    prompt_start = content.find('"""') + 3
    prompt_end = content.rfind('"""')
    
    if prompt_start == -1 or prompt_end == -1:
        # Try alternative markers
        lines = content.split('\n')
        prompt_lines = []
        in_prompt = False
        
        for line in lines:
            if '='*40 in line and 'OPTIMIZED' in line:
                in_prompt = True
                continue
            if '='*40 in line and 'INSTRUCTIONS' in line:
                break
            if in_prompt and line.strip():
                prompt_lines.append(line)
        
        optimized_prompt = '\n'.join(prompt_lines)
    else:
        optimized_prompt = content[prompt_start:prompt_end]
    
    # Read current engine.py
    engine_file = Path("app/services/scoring/engine.py")
    
    with open(engine_file, 'r') as f:
        engine_content = f.read()
    
    # Find and replace the prompt in get_sfia_rubric_prompt method
    # Look for the return statement with the prompt
    pattern = r'return f"""(.*?)"""'
    
    def replace_prompt(match):
        return f'return f"""{optimized_prompt}"""'
    
    updated_content = re.sub(pattern, replace_prompt, engine_content, flags=re.DOTALL)
    
    # Backup original
    backup_file = engine_file.with_suffix('.py.backup')
    with open(backup_file, 'w') as f:
        f.write(engine_content)
    
    # Write updated version
    with open(engine_file, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Updated prompt in {engine_file}")
    print(f"📁 Backup saved to {backup_file}")
    print(f"\n⚠️  IMPORTANT: Review the changes before committing!")
    print(f"   Run: python run_evaluation.py optimized")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python apply_optimized_prompt.py <path_to_optimized_prompt.txt>")
        sys.exit(1)
    
    apply_optimized_prompt(sys.argv[1])