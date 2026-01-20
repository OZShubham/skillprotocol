import os
import ast
import hashlib
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
from opik import track  # <--- NEW IMPORT

# --- CONFIGURATION ---
NCRF_HOURS_PER_CREDIT = 30

# FIXED: Different complexity tiers have different learning curves
LEARNING_HOURS_PER_100_SLOC = {
    "simple": 2,      # Basic scripts (print, variables)
    "moderate": 5,    # Functions, logic, file I/O
    "complex": 10,    # Classes, async, algorithms
    "advanced": 20    # Architecture, design patterns, optimization
}

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".go", ".rs", 
    ".ps1", ".sh", ".bash", ".rb", ".php", ".c", ".h", ".css", ".html", 
    ".sql", ".yaml", ".yml", ".json", ".toml", ".ipynb" 
}
MAX_ESTIMATED_HOURS = 200  
MIN_SFIA_LEVEL = 1
MAX_SFIA_LEVEL = 5  # FIXED: GitHub can only prove up to Level 5 (not 6-7)

# FIXED: More conservative multipliers based on REAL SFIA definitions
SFIA_MULTIPLIERS = {
    1: 0.5,   # Follow: Basic syntax, scripts
    2: 0.8,   # Assist: Working code, needs guidance
    3: 1.0,   # Apply: Standard professional work (BASELINE)
    4: 1.3,   # Enable: Complex patterns, mentorship-ready code
    5: 1.7,   # Ensure: Production systems, architecture
}

class ScoringEngine:
    
    def _get_repo_fingerprint(self, repo_path: str, file_count: int) -> str:
        """Generates a hash based on path AND file count."""
        raw_id = f"{repo_path}_{file_count}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:8]

    def _count_sloc(self, file_content: str, ext: str) -> int:
        """Count Source Lines of Code (logical, not physical)"""
        try:
            if ext == ".py":
                tree = ast.parse(file_content)
                logical_lines = set()
                for node in ast.walk(tree):
                    if isinstance(node, (ast.stmt, ast.expr)) and hasattr(node, 'lineno'):
                        logical_lines.add(node.lineno)
                return len(logical_lines)
            else:
                return len([line for line in file_content.splitlines() 
                            if line.strip() and not line.strip().startswith(('//', '#', '/*'))])
        except Exception:
            return 0

    def _estimate_complexity_tier(self, file_content: str, ext: str) -> str:
        """
        FIXED: Determines if code is simple/moderate/complex/advanced
        This affects NCrF learning hours calculation
        """
        if ext != ".py":
            return "moderate"  # Default for non-Python
        
        try:
            tree = ast.parse(file_content)
            complexity_score = 0
            
            for node in ast.walk(tree):
                # Simple indicators
                if isinstance(node, (ast.For, ast.While, ast.If)):
                    complexity_score += 1
                
                # Moderate indicators
                if isinstance(node, ast.FunctionDef):
                    complexity_score += 2
                
                # Complex indicators
                if isinstance(node, (ast.ClassDef, ast.Try, ast.With)):
                    complexity_score += 3
                
                # Advanced indicators
                if isinstance(node, (ast.AsyncFunctionDef, ast.Lambda)):
                    complexity_score += 5
                if isinstance(node, ast.Decorator):
                    complexity_score += 4
            
            # Normalize by file length
            sloc = self._count_sloc(file_content, ext)
            if sloc == 0:
                return "simple"
            
            score_per_line = complexity_score / sloc
            
            if score_per_line < 0.1:
                return "simple"
            elif score_per_line < 0.3:
                return "moderate"
            elif score_per_line < 0.6:
                return "complex"
            else:
                return "advanced"
                
        except Exception:
            return "moderate"

    @track(name="Detect SFIA Markers", type="tool") # <--- NEW DECORATOR
    def _detect_sfia_markers(self, repo_path: str) -> Dict[str, Any]:
        """
        Scans for SFIA capability markers.
        FIXED: More realistic criteria for each level.
        """
        markers = {
            # Level 3 markers (Professional baseline)
            "has_readme": False,
            "has_requirements": False,
            "has_modular_structure": False,  # Multiple files
            
            # Level 4 markers (Enable - mentorship-ready)
            "has_tests": False,
            "has_docstrings": False,
            "uses_design_patterns": False,
            
            # Level 5 markers (Ensure - production)
            "has_ci_cd": False,
            "has_docker": False,
            "has_error_handling": False,
            "uses_async": False,
            
            # Metadata
            "file_count": 0,
            "code_samples": []
        }
        
        repo_files = list(Path(repo_path).rglob('*'))
        markers["file_count"] = len([f for f in repo_files if f.suffix in CODE_EXTENSIONS])
        
        # Modular structure check
        if markers["file_count"] >= 3:
            markers["has_modular_structure"] = True
        
        for file_path in repo_files:
            filename = file_path.name.lower()
            
            # Level 3 checks
            if filename in ['readme.md', 'readme.rst', 'readme.txt']:
                markers["has_readme"] = True
            if filename in ['requirements.txt', 'package.json', 'go.mod', 'cargo.toml']:
                markers["has_requirements"] = True
            
            # Level 4 checks
            if 'test' in str(file_path) or filename.startswith('test_'):
                markers["has_tests"] = True
            
            # Level 5 checks
            if filename == 'dockerfile' or filename == 'docker-compose.yml':
                markers["has_docker"] = True
            if '.github/workflows' in str(file_path) or '.gitlab-ci.yml' in filename:
                markers["has_ci_cd"] = True
        
        # Python-specific analysis
        python_files = [f for f in repo_files if f.suffix == '.py']
        
        for py_file in python_files[:5]:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        # Level 4 indicators
                        if isinstance(node, ast.ClassDef):
                            markers["uses_design_patterns"] = True
                        
                        # Level 5 indicators
                        if isinstance(node, ast.AsyncFunctionDef):
                            markers["uses_async"] = True
                        if isinstance(node, ast.Try):
                            markers["has_error_handling"] = True
                        
                        # Docstring check
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if ast.get_docstring(node):
                                markers["has_docstrings"] = True
                    
                    # Store sample
                    if len(markers["code_samples"]) < 2:
                        markers["code_samples"].append({
                            "file": py_file.name,
                            "snippet": content[:800]
                        })
                        
            except Exception:
                continue
        
        return markers

    @track(name="Calculate NCrF Base Credits", type="tool") # <--- NEW DECORATOR
    def calculate_ncrf_base_credits(self, repo_path: str) -> Dict[str, Any]:
        """
        FIXED NCrF Calculation: Estimates LEARNING hours, not writing hours.
        Uses complexity tiers to weight the learning effort.
        """
        total_sloc = 0
        weighted_learning_hours = 0
        file_count = 0
        complexity_distribution = {"simple": 0, "moderate": 0, "complex": 0, "advanced": 0}
        
        for root, _, files in os.walk(repo_path):
            if any(skip in root for skip in ['node_modules', 'venv', '__pycache__', '.git']):
                continue
                
            for file in files:
                _, ext = os.path.splitext(file)
                if ext not in CODE_EXTENSIONS:
                    continue
                    
                try:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        sloc = self._count_sloc(content, ext)
                        tier = self._estimate_complexity_tier(content, ext)
                        
                        total_sloc += sloc
                        file_count += 1
                        complexity_distribution[tier] += sloc
                        
                        # Calculate weighted learning hours
                        hours_per_100_sloc = LEARNING_HOURS_PER_100_SLOC[tier]
                        weighted_learning_hours += (sloc / 100) * hours_per_100_sloc
                        
                except Exception:
                    pass

        estimated_hours = min(weighted_learning_hours, MAX_ESTIMATED_HOURS)
        base_credits = estimated_hours / NCRF_HOURS_PER_CREDIT

        return {
            "repo_fingerprint": self._get_repo_fingerprint(repo_path, file_count),
            "files_scanned": file_count,
            "total_sloc": total_sloc,
            "complexity_distribution": complexity_distribution,
            "estimated_learning_hours": round(estimated_hours, 2),
            "ncrf_base_credits": round(base_credits, 2),
            "capped": weighted_learning_hours > MAX_ESTIMATED_HOURS
        }

    def get_sfia_rubric_prompt(self, ncrf_stats: Dict, markers: Dict) -> str:
        """
        FIXED: Uses REAL SFIA definitions focused on autonomy and responsibility.
        """
        
        # **FIX: Extract code_samples separately, with safe fallback**
        code_samples = markers.get("code_samples", [])
        
        # Build the prompt
        return f"""You are a Senior Technical Auditor using SFIA (Skills Framework for the Information Age) to assess developer capability.

    **Repository Statistics:**
    - Files: {ncrf_stats['files_scanned']}
    - Total SLOC: {ncrf_stats['total_sloc']}
    - Complexity: {ncrf_stats['complexity_distribution']}
    - Learning Hours: {ncrf_stats['estimated_learning_hours']}

    **Evidence Detected:**
    ✓ README: {markers.get('has_readme', False)}
    ✓ Dependencies defined: {markers.get('has_requirements', False)}
    ✓ Modular (3+ files): {markers.get('has_modular_structure', False)}
    ✓ Tests: {markers.get('has_tests', False)}
    ✓ Docstrings: {markers.get('has_docstrings', False)}
    ✓ Design Patterns (OOP): {markers.get('uses_design_patterns', False)}
    ✓ CI/CD: {markers.get('has_ci_cd', False)}
    ✓ Docker: {markers.get('has_docker', False)}
    ✓ Error Handling: {markers.get('has_error_handling', False)}
    ✓ Async/Advanced: {markers.get('uses_async', False)}

    **SFIA Levels (GitHub-Provable):**
    Level 1 - Follow: Single-file scripts, no structure, basic syntax only.
    Level 2 - Assist: Multiple files with functions, but missing README/requirements. Needs guidance.
    Level 3 - Apply: ✓README + ✓Requirements + ✓Modular. Professional baseline. Works independently.
    Level 4 - Enable: ✓Level 3 + ✓Tests + ✓Docstrings + OOP. Can mentor juniors. Complex problem-solving.
    Level 5 - Ensure: ✓Level 4 + ✓CI/CD + ✓Docker + Production patterns. Owns system reliability.

    NOTE: Levels 6-7 require organizational impact evidence (not provable from code alone).

    **Code Sample:**
    {json.dumps(code_samples[:1], indent=2) if code_samples else "No code samples available"}

    **Task:** Assign ONE level (1-5) based on EVIDENCE, not potential. Be conservative.

    **Respond ONLY with valid JSON:**
    {{
    "sfia_level": 3,
    "reasoning": "Clear explanation linking evidence to level",
    "evidence_used": ["README present", "No tests found"],
    "missing_for_next_level": ["Unit tests required for L4"]
    }}
    """

    def finalize_score(
        self, 
        ncrf_data: Dict, 
        sfia_markers: Dict,
        llm_sfia_response_json: str,
        reality_check_passed: bool = True
    ) -> Dict[str, Any]:
        """
        Combines NCrF (learning hours) + SFIA (capability) + Reality Check (works).
        """
        try:
            sfia_data = json.loads(llm_sfia_response_json)
            raw_level = sfia_data.get("sfia_level", 3)
            level = max(MIN_SFIA_LEVEL, min(MAX_SFIA_LEVEL, int(raw_level)))
            
            multiplier = SFIA_MULTIPLIERS.get(level, 1.0)
            reality_multiplier = 1.0 if reality_check_passed else 0.5
            
            final_credits = ncrf_data["ncrf_base_credits"] * multiplier * reality_multiplier

            return {
                "status": "success",
                "final_verified_credits": round(final_credits, 2),
                "audit_trail": {
                    "repo_hash": ncrf_data["repo_fingerprint"],
                    "ncrf_data": ncrf_data,
                    "sfia_assessment": {
                        "level": level,
                        "level_name": self._get_sfia_level_name(level),
                        "multiplier": f"{multiplier}x",
                        "reasoning": sfia_data.get("reasoning"),
                        "evidence": sfia_data.get("evidence_used", []),
                        "next_steps": sfia_data.get("missing_for_next_level", [])
                    },
                    "reality_check": {
                        "passed": reality_check_passed,
                        "penalty_applied": not reality_check_passed
                    },
                    "markers_detected": {k: v for k, v in sfia_markers.items() if k != "code_samples"}
                }
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error", 
                "message": f"LLM returned invalid JSON: {str(e)}",
                "raw_response": llm_sfia_response_json[:500]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _get_sfia_level_name(self, level: int) -> str:
        """Returns SFIA level name"""
        names = {
            1: "Follow", 2: "Assist", 3: "Apply", 
            4: "Enable", 5: "Ensure"
        }
        return names.get(level, "Unknown")


# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    engine = ScoringEngine()
    
    # Example repo path (replace with actual path)
    test_repo = "/path/to/repo"
    
    print("=" * 60)
    print("SKILLPROTOCOL - NCrF + SFIA CREDIT ENGINE")
    print("=" * 60)
    
    # Step 1: NCrF Calculation
    print("\n[1/4] Calculating NCrF Base Credits...")
    ncrf_result = engine.calculate_ncrf_base_credits(test_repo)
    print(json.dumps(ncrf_result, indent=2))
    
    # Step 2: SFIA Marker Detection
    print("\n[2/4] Detecting SFIA Capability Markers...")
    markers = engine._detect_sfia_markers(test_repo)
    print(json.dumps({k: v for k, v in markers.items() if k != "code_samples"}, indent=2))
    
    # Step 3: Generate LLM Prompt
    print("\n[3/4] Generating SFIA Assessment Prompt...")
    prompt = engine.get_sfia_rubric_prompt(ncrf_result, markers)
    print(prompt[:500] + "...\n")
    
    # Step 4: (Mock LLM response for demo)
    print("[4/4] Finalizing Score (using mock LLM response)...")
    mock_llm = json.dumps({
        "sfia_level": 4,
        "reasoning": "Has README, requirements, tests, and OOP patterns. Missing CI/CD for L5.",
        "evidence_used": ["README.md", "tests/ directory", "Class definitions"],
        "missing_for_next_level": ["CI/CD pipeline", "Docker"]
    })
    
    final = engine.finalize_score(ncrf_result, markers, mock_llm, reality_check_passed=True)
    print(json.dumps(final, indent=2))