"""
Enhanced Scoring Engine with Tree-sitter Multi-Language Support
Supports: Python, TypeScript, JavaScript, Java, Go, Rust, C++, Ruby, PHP, and more
"""

import os
import hashlib
import json
import math
import re
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from opik import track

# Tree-sitter imports - Individual language bindings
try:
    import tree_sitter
    # Import the Language class specifically for wrapping raw pointers
    from tree_sitter import Language, Parser
    
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_java
    import tree_sitter_go
    import tree_sitter_rust
    import tree_sitter_cpp
    import tree_sitter_c
    import tree_sitter_ruby
    import tree_sitter_php
    import tree_sitter_c_sharp
    TREE_SITTER_AVAILABLE = True
except ImportError as e:
    TREE_SITTER_AVAILABLE = False
    print(f"⚠️  Tree-sitter not available: {e}. Falling back to basic analysis.")

# Configuration
NCRF_HOURS_PER_CREDIT = 30

LEARNING_HOURS_PER_100_SLOC = {
    "simple": 2,
    "moderate": 5,
    "complex": 10,
    "advanced": 20
}

# Supported languages with Tree-sitter
LANGUAGE_CONFIGS = {
    '.py': {'name': 'python'},
    '.js': {'name': 'javascript'},
    '.ts': {'name': 'typescript'},
    '.tsx': {'name': 'typescript'}, # Analyze TSX as Typescript
    '.jsx': {'name': 'javascript'},
    '.java': {'name': 'java'},
    '.go': {'name': 'go'},
    '.rs': {'name': 'rust'},
    '.cpp': {'name': 'cpp'},
    '.c': {'name': 'c'},
    '.rb': {'name': 'ruby'},
    '.php': {'name': 'php'},
    '.cs': {'name': 'csharp'},
}

# Fallback extensions (no Tree-sitter, basic analysis)
FALLBACK_EXTENSIONS = {
    '.sh', '.bash', '.css', '.html', '.sql', 
    '.yaml', '.yml', '.json', '.toml', '.md'
}

CODE_EXTENSIONS = set(LANGUAGE_CONFIGS.keys()) | FALLBACK_EXTENSIONS

# --- FIX 1: IGNORE LIST FOR LOCKFILES ---
IGNORED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 
    'cargo.lock', 'poetry.lock', 'composer.lock', 
    'tsconfig.json', 'jsconfig.json', 'go.sum'
}

MAX_ESTIMATED_HOURS = 200
MIN_SFIA_LEVEL = 1
MAX_SFIA_LEVEL = 5

SFIA_MULTIPLIERS = {
    1: 0.5,
    2: 0.8,
    3: 1.0,
    4: 1.3,
    5: 1.7,
}


class UniversalCodeAnalyzer:
    """
    Universal code analyzer using Tree-sitter
    Works across 15+ programming languages
    """
    
    def __init__(self):
        self.parsers = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize Tree-sitter parsers using VERIFIED binding names"""
        if not TREE_SITTER_AVAILABLE:
            return

        # --- FIX 2: HARDCODED BINDINGS BASED ON YOUR LOGS ---
        # Map extension -> (Module, Function_Name)
        bindings_map = {
            # Standard 'language' attribute
            '.py': (tree_sitter_python, 'language'),
            '.js': (tree_sitter_javascript, 'language'),
            '.jsx': (tree_sitter_javascript, 'language'),
            '.java': (tree_sitter_java, 'language'),
            '.go': (tree_sitter_go, 'language'),
            '.rs': (tree_sitter_rust, 'language'),
            '.cpp': (tree_sitter_cpp, 'language'),
            '.c': (tree_sitter_c, 'language'),
            '.rb': (tree_sitter_ruby, 'language'),
            '.cs': (tree_sitter_c_sharp, 'language'),
            
            # Special cases from your logs
            '.ts': (tree_sitter_typescript, 'language_typescript'),
            '.tsx': (tree_sitter_typescript, 'language_tsx'), 
            '.php': (tree_sitter_php, 'language_php'),
        }

        for ext, (module, attr_name) in bindings_map.items():
            try:
                # 1. Get the language object
                if not hasattr(module, attr_name):
                    # Try fallback to 'language' if specific failed
                    if hasattr(module, 'language'):
                        attr_name = 'language'
                    else:
                        # print(f"⚠️  Binding mismatch: {module} has no '{attr_name}'")
                        continue
                    
                candidate = getattr(module, attr_name)
                # Get the raw C-pointer (PyCapsule)
                native_ptr = candidate() if callable(candidate) else candidate

                # 2. THE CRITICAL FIX: Wrap in Language()
                lang_wrapper = tree_sitter.Language(native_ptr)

                # 3. Initialize Parser with the wrapper
                parser = tree_sitter.Parser(lang_wrapper)
                
                self.parsers[ext] = parser
                # print(f"✅ Loaded {ext} parser")

            except Exception as e:
                # print(f"⚠️  Failed to load {ext}: {e}")
                pass

    def analyze_file(self, file_content: str, ext: str) -> Dict[str, Any]:
        """Analyze a code file"""
        # Auto-detect TSX from content if extension is ambiguous
        if ext == '.ts' and 'React' in file_content and '</' in file_content:
            if '.tsx' in self.parsers:
                return self._analyze_with_treesitter(file_content, '.tsx')

        if ext in self.parsers:
            return self._analyze_with_treesitter(file_content, ext)
        else:
            return self._fallback_analysis(file_content, ext)

    def _analyze_with_treesitter(self, content: str, ext: str) -> Dict[str, Any]:
        """Tree-sitter based analysis"""
        try:
            parser = self.parsers[ext]
            
            # Robust parsing (handles bytes vs string diffs in versions)
            try:
                tree = parser.parse(bytes(content, 'utf8', errors='ignore'))
            except TypeError:
                tree = parser.parse(content)
            
            metrics = {
                'sloc': 0,
                'complexity': 1,
                'patterns': {
                    'has_classes': False,
                    'has_async': False,
                    'has_error_handling': False,
                    'has_interfaces': False,
                    'has_generics': False,
                    'has_decorators': False,
                }
            }
            
            lines_seen = set()
            for node in self._walk_tree(tree.root_node):
                # SLOC
                if node.start_point[0] not in lines_seen:
                    lines_seen.add(node.start_point[0])
                    metrics['sloc'] += 1
                
                node_type = node.type
                
                # Classes / Interfaces
                if node_type in ['class_definition', 'class_declaration', 'interface_declaration', 'struct_specifier']:
                    metrics['patterns']['has_classes'] = True
                    metrics['complexity'] += 3
                
                # Async
                elif 'async' in node_type or node_type in ['await_expression', 'goroutine_statement']:
                    metrics['patterns']['has_async'] = True
                    metrics['complexity'] += 2
                
                # Error Handling
                elif node_type in ['try_statement', 'catch_clause', 'except_clause', 'rescue_modifier']:
                    metrics['patterns']['has_error_handling'] = True
                    metrics['complexity'] += 1
                
                # Complexity Points
                elif node_type in ['if_statement', 'for_statement', 'while_statement', 'case_statement']:
                    metrics['complexity'] += 1
                elif node_type in ['function_definition', 'method_definition', 'func_literal']:
                    metrics['complexity'] += 1
            
            # Calculate tier
            density = metrics['complexity'] / max(1, metrics['sloc'])
            if density < 0.05: metrics['tier'] = 'simple'
            elif density < 0.10: metrics['tier'] = 'moderate'
            else: metrics['tier'] = 'complex'
            
            return metrics
            
        except Exception:
            return self._fallback_analysis(content, ext)

    def _fallback_analysis(self, content: str, ext: str) -> Dict[str, Any]:
        """Regex-based fallback"""
        sloc = len([l for l in content.splitlines() if l.strip()])
        # Basic regex check
        patterns = {
            'has_classes': bool(re.search(r'\b(class|interface|struct)\b', content)),
            'has_async': bool(re.search(r'\b(async|await|go func)\b', content)),
            'has_error_handling': bool(re.search(r'\b(try|catch|except|defer|rescue)\b', content)),
            'has_interfaces': False, 
            'has_generics': False, 
            'has_decorators': False
        }
        return {'sloc': sloc, 'complexity': max(1, sloc // 10), 'tier': 'moderate', 'patterns': patterns}

    def _walk_tree(self, node):
        yield node
        for child in node.children:
            yield from self._walk_tree(child)


class ScoringEngine:
    """
    Enhanced Scoring Engine with multi-language support
    """
    
    def __init__(self):
        self.analyzer = UniversalCodeAnalyzer()
    
    # def _get_repo_fingerprint(self, repo_path: str, file_count: int) -> str:
    #     """Generate unique repo fingerprint"""
    #     raw_id = f"{repo_path}_{file_count}"
    #     return hashlib.md5(raw_id.encode()).hexdigest()[:8]
    
    def _get_repo_fingerprint(self, repo_path: str) -> str:
        """Generate fingerprint based on the actual latest commit hash."""
        try:
            import git
            repo = git.Repo(repo_path)
            # Use the SHA of the latest commit on the current branch
            return repo.head.object.hexsha
        except Exception:
            # Fallback to a content hash of the file list if git fails
            files = sorted([str(p) for p in Path(repo_path).rglob('*') if p.is_file()])
            return hashlib.md5("".join(files).encode()).hexdigest()
        
    @track(name="Calculate NCrF Base Credits (Enhanced)", type="tool")
    def calculate_ncrf_base_credits(self, repo_path: str) -> Dict[str, Any]:
        """
        Enhanced NCrF calculation with multi-language support
        """
        
        total_sloc = 0
        total_complexity = 0
        weighted_learning_hours = 0
        file_count = 0
        
        # Language breakdown
        language_stats = {}
        complexity_distribution = {
            "simple": 0, "moderate": 0, "complex": 0, "advanced": 0
        }
        
        # Pattern aggregation
        global_patterns = {
            'has_classes': False, 'has_async': False, 'has_error_handling': False,
            'has_interfaces': False, 'has_generics': False, 'has_decorators': False,
        }
        
        print(f"🔬 [Enhanced Scanner] Analyzing repository with Tree-sitter...")
        
        for root, _, files in os.walk(repo_path):
            # Skip common directories
            if any(skip in root for skip in ['node_modules', 'venv', '__pycache__', '.git', 'dist', 'build', '.next']):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                file_lower = file.lower()
                # --- FIX 1: EXPLICIT LOCKFILE IGNORE ---
                if any(ignored in file_lower for ignored in IGNORED_FILES):
                   continue
                    
                _, ext = os.path.splitext(file)
                
                if ext not in CODE_EXTENSIONS:
                    continue
                
                try:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Analyze
                    metrics = self.analyzer.analyze_file(content, ext)
                    
                    sloc = metrics['sloc']
                    complexity = metrics['complexity']
                    tier = metrics['tier']
                    
                    # Aggregate metrics
                    total_sloc += sloc
                    total_complexity += complexity
                    file_count += 1
                    complexity_distribution[tier] += sloc
                    
                    # Track language usage
                    lang_name = LANGUAGE_CONFIGS.get(ext, {}).get('name', ext)
                    if lang_name not in language_stats:
                        language_stats[lang_name] = {'files': 0, 'sloc': 0}
                    language_stats[lang_name]['files'] += 1
                    language_stats[lang_name]['sloc'] += sloc
                    
                    # Aggregate patterns
                    for pattern, detected in metrics['patterns'].items():
                        if detected:
                            global_patterns[pattern] = True
                    
                    # Calculate weighted learning hours
                    hours_per_100 = LEARNING_HOURS_PER_100_SLOC[tier]
                    weighted_learning_hours += (sloc / 100) * hours_per_100
                    
                except Exception as e:
                    # print(f"⚠️  Error analyzing {file}: {e}")
                    continue
        
        # Calculate final metrics
        estimated_hours = min(weighted_learning_hours, MAX_ESTIMATED_HOURS)
        base_credits = estimated_hours / NCRF_HOURS_PER_CREDIT
        
        # Enhanced Maintainability Index
        avg_mi = self._calculate_enhanced_mi(total_sloc, total_complexity)
        complexity_density = total_complexity / max(1, total_sloc)
        
        # Dominant language
        dominant_lang = max(language_stats.items(), key=lambda x: x[1]['sloc'])[0] if language_stats else 'Unknown'
        
        result = {
            "repo_fingerprint": self._get_repo_fingerprint(repo_path),
            "files_scanned": file_count,
            "total_sloc": total_sloc,
            "total_complexity": total_complexity,
            "avg_mi": avg_mi,
            "complexity_density": round(complexity_density, 4),
            "complexity_distribution": complexity_distribution,
            "estimated_learning_hours": round(estimated_hours, 2),
            "ncrf_base_credits": round(base_credits, 2),
            "capped": weighted_learning_hours > MAX_ESTIMATED_HOURS,
            
            # New fields
            "language_stats": language_stats,
            "dominant_language": dominant_lang,
            "global_patterns": global_patterns,
        }
        
        # Print summary
        print(f"   Languages detected: {', '.join(language_stats.keys())}")
        if dominant_lang != 'Unknown':
            print(f"   Dominant: {dominant_lang} ({language_stats[dominant_lang]['sloc']} SLOC)")
        print(f"   Patterns: Classes={global_patterns['has_classes']}, Async={global_patterns['has_async']}")
        
        return result
    
    def _calculate_enhanced_mi(self, sloc: int, complexity: int) -> float:
        """Enhanced Maintainability Index calculation"""
        if sloc == 0: return 65.0
        
        complexity_per_line = complexity / sloc
        
        if sloc < 1000:
            if complexity_per_line < 0.05: base_mi = 80
            elif complexity_per_line < 0.10: base_mi = 60
            else: base_mi = 45
        else:
            if complexity_per_line < 0.06: base_mi = 75
            elif complexity_per_line < 0.12: base_mi = 65
            else: base_mi = 50
            
        return round(min(100.0, max(0.0, base_mi)), 2)
    
    @track(name="Detect SFIA Markers (Enhanced)", type="tool")
    def _detect_sfia_markers(self, repo_path: str) -> Dict[str, Any]:
        """Enhanced SFIA marker detection"""
        
        # First, run NCrF analysis to get global patterns
        ncrf_data = self.calculate_ncrf_base_credits(repo_path)
        global_patterns = ncrf_data.get('global_patterns', {})
        
        markers = {
            "has_readme": False,
            "has_requirements": False,
            "has_modular_structure": ncrf_data['files_scanned'] >= 3,
            "has_tests": False,
            "has_docstrings": False,
            "uses_design_patterns": global_patterns.get('has_classes', False) or global_patterns.get('has_interfaces', False),
            "has_ci_cd": False,
            "has_docker": False,
            "has_error_handling": global_patterns.get('has_error_handling', False),
            "uses_async": global_patterns.get('has_async', False),
            "uses_generics": global_patterns.get('has_generics', False),
            "uses_decorators": global_patterns.get('has_decorators', False),
            "file_count": ncrf_data['files_scanned'],
            "code_samples": []
        }
        
        # File-based markers
        repo_files = list(Path(repo_path).rglob('*'))
        
        for file_path in repo_files:
            filename = file_path.name.lower()
            path_str = str(file_path).lower()
            
            if filename in ['readme.md', 'readme.rst', 'readme.txt']:
                markers["has_readme"] = True
            
            if filename in ['requirements.txt', 'package.json', 'go.mod', 'cargo.toml', 'pom.xml', 'build.gradle', 'pyproject.toml']:
                markers["has_requirements"] = True
            
            if 'test' in path_str or filename.startswith('test_') or filename.endswith('_test.py') or filename.endswith('.test.ts') or filename.endswith('.spec.ts'):
                markers["has_tests"] = True
            
            if '.github/workflows' in path_str or '.gitlab-ci.yml' in filename or 'jenkinsfile' in filename:
                markers["has_ci_cd"] = True
            
            if filename in ['dockerfile', 'docker-compose.yml', 'docker-compose.yaml']:
                markers["has_docker"] = True
        
        return markers
    
    # --- CRITICAL FIX: ACCEPT statistical_hint AS 3RD ARGUMENT ---
    def get_sfia_rubric_prompt(self, ncrf_stats: Dict, markers: Dict, statistical_hint: Dict = None) -> str:
        """
        Enhanced SFIA prompt with language-specific context AND Statistical Anchoring
        """
        
        language_stats = ncrf_stats.get('language_stats', {})
        dominant_lang = ncrf_stats.get('dominant_language', 'Unknown')
        
        lang_context = f"**Primary Language:** {dominant_lang}\n"
        if len(language_stats) > 1:
            lang_context += "**Multi-language project** with:\n"
            for lang, stats in sorted(language_stats.items(), key=lambda x: x[1]['sloc'], reverse=True):
                lang_context += f"  - {lang}: {stats['sloc']} SLOC ({stats['files']} files)\n"

        # --- STATISTICAL ANCHOR BLOCK ---
        stats_context = ""
        if statistical_hint:
            s_level = statistical_hint['suggested_level']
            s_conf = statistical_hint['confidence']
            s_range = statistical_hint['plausible_range']
            
            stats_context = f"""
            **📊 Statistical Prior (Bayesian Model):**
            - Based on code metrics (SLOC: {ncrf_stats['total_sloc']}, MI: {ncrf_stats['avg_mi']}), the math suggests **Level {s_level}** ({s_conf:.1%} confidence).
            - Plausible Range: Levels {min(s_range)} to {max(s_range)}.
            - **INSTRUCTION:** If you deviate from Level {s_level}, you MUST provide strong evidence (e.g., specific advanced patterns) in the 'reasoning' field to justify why the metrics are misleading.
            """
        else:  # ✅ ADD THIS ELSE BLOCK
           stats_context = """
            **📊 Statistical Prior (Bayesian Model):**
            - No statistical baseline available. Use evidence-based assessment only.
            """
                    # -------------------------------------
            
        return f"""You are a Senior Technical Auditor using SFIA (Skills Framework for the Information Age) to assess developer capability.

    **Repository Statistics:**
    - Files: {ncrf_stats['files_scanned']}
    - Total SLOC: {ncrf_stats['total_sloc']}
    - Complexity: {ncrf_stats['total_complexity']} ({ncrf_stats['complexity_density']:.3f} per line)
    - Maintainability Index: {ncrf_stats['avg_mi']}/100
    - Learning Hours: {ncrf_stats['estimated_learning_hours']}

    {lang_context}
    {stats_context}

    **Evidence Detected:**
    ✓ README: {markers.get('has_readme', False)}
    ✓ Dependencies defined: {markers.get('has_requirements', False)}
    ✓ Modular (3+ files): {markers.get('has_modular_structure', False)}
    ✓ Tests: {markers.get('has_tests', False)}
    ✓ Docstrings: {markers.get('has_docstrings', False)}
    ✓ Design Patterns (OOP/Interfaces): {markers.get('uses_design_patterns', False)}
    ✓ CI/CD: {markers.get('has_ci_cd', False)}
    ✓ Docker: {markers.get('has_docker', False)}
    ✓ Error Handling: {markers.get('has_error_handling', False)}
    ✓ Async/Concurrent: {markers.get('uses_async', False)}
    ✓ Generics/Templates: {markers.get('uses_generics', False)}

    **SFIA Levels (GitHub-Provable):**
    Level 1 - Follow: Single-file scripts, no structure, basic syntax only.
    Level 2 - Assist: Multiple files with functions, but missing README/requirements. Needs guidance.
    Level 3 - Apply: ✓README + ✓Requirements + ✓Modular. Professional baseline. Works independently.
    Level 4 - Enable: ✓Level 3 + ✓Tests + ✓Design Patterns + Error Handling. Can mentor juniors.
    Level 5 - Ensure: ✓Level 4 + ✓CI/CD + ✓Docker + Production patterns. Owns system reliability.

    **Task:** Assign ONE level (1-5) based on EVIDENCE, not potential. Consider the multi-language nature and complexity.

    **Respond ONLY with valid JSON:**
    {{
    "sfia_level": 3,
    "confidence": 0.85,
    "reasoning": "Clear explanation linking evidence to level",
    "evidence_used": ["README present", "Multi-language structure"],
    "missing_for_next_level": ["Unit tests required for L4"]
    }}
    """
    
    def finalize_score(self, ncrf_data: Dict, sfia_markers: Dict, llm_sfia_response_json: str, reality_check_passed: bool = True) -> Dict[str, Any]:
        """Final score calculation with enhanced audit trail"""
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
                    "repo_hash": ncrf_data.get("repo_fingerprint", "unknown"),
                    "ncrf_data": ncrf_data,
                    "sfia_assessment": {
                        "level": level, 
                        "level_name": self._get_sfia_level_name(level),
                        "multiplier": f"{multiplier}x",
                        "confidence": sfia_data.get("confidence", 0.85),
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
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_sfia_level_name(self, level: int) -> str:
        names = {1: "Follow", 2: "Assist", 3: "Apply", 4: "Enable", 5: "Ensure"}
        return names.get(level, "Unknown")