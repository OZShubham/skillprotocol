"""
Enhanced Pattern Detector - Understands CODE QUALITY, not just syntax
Add this to your ScoringEngine to detect ANTI-PATTERNS and BEST PRACTICES
"""

import re
from typing import Dict, List, Tuple

class CodeQualityAnalyzer:
    """
    Detects patterns that Tree-sitter CAN'T see:
    - Anti-patterns (code smells)
    - Best practices (design patterns used correctly)
    - Domain sophistication (algorithms, architecture)
    """
    
    def __init__(self):
        # RED FLAGS (reduce credits)
        self.anti_patterns = {
            'god_object': r'class\s+\w+.*\n(?:.*\n){200,}',  # >200 line class
            'magic_numbers': r'\b\d{3,}\b(?!\s*#)',  # Hardcoded numbers
            'swallowed_exceptions': r'except.*:\s*pass',
            'global_state': r'global\s+\w+',
            'blocking_sleep': r'time\.sleep\(\d+\)',
            'todos_in_prod': r'TODO|FIXME|HACK',
            'no_type_hints': True,  # Checked separately
        }
        
        # GREEN FLAGS (boost credits)
        self.best_practices = {
            'dependency_injection': r'def\s+__init__\(self.*:\s*\w+',
            'factory_pattern': r'def\s+create_\w+\(',
            'builder_pattern': r'class\s+\w+Builder',
            'strategy_pattern': r'class\s+\w+Strategy',
            'proper_logging': r'logging\.\w+\(',
            'type_annotations': r'def\s+\w+\([^)]*:\s*\w+',
            'docstrings': r'"""[\s\S]*?"""',
            'unit_test_assertions': r'assert_\w+\(',
        }
        
        # ALGORITHM SOPHISTICATION
        self.advanced_algorithms = {
            'dynamic_programming': [
                r'memo\s*=\s*\{',
                r'@lru_cache',
                r'dp\s*=\s*\[',
            ],
            'graph_algorithms': [
                r'dijkstra|bellman|floyd|kruskal|prim',
                r'adjacency\s*(list|matrix)',
                r'bfs|dfs\s*\(',
            ],
            'concurrency_patterns': [
                r'asyncio\.',
                r'ThreadPoolExecutor|ProcessPoolExecutor',
                r'Queue\(\)|Lock\(\)',
                r'async\s+def.*await',
            ],
            'data_structures': [
                r'heap\w+|priority_queue',
                r'trie|suffix_tree',
                r'bloom_filter|lru_cache',
            ]
        }
    
    def analyze_code_quality(self, content: str, file_path: str) -> Dict:
        """
        Returns a QUALITY SCORE that considers:
        - Anti-patterns (bad practices)
        - Best practices (good design)
        - Algorithm sophistication
        """
        
        results = {
            'quality_score': 1.0,  # Multiplier (0.5 - 2.0)
            'red_flags': [],
            'green_flags': [],
            'sophistication_level': 'basic',
            'reasoning': []
        }
        
        # 1. DETECT ANTI-PATTERNS (penalties)
        penalties = 0
        for pattern_name, regex in self.anti_patterns.items():
            if isinstance(regex, bool):
                continue  # Handle separately
            
            matches = re.findall(regex, content, re.MULTILINE)
            if matches:
                penalties += len(matches) * 0.05  # 5% per occurrence
                results['red_flags'].append(f"{pattern_name}: {len(matches)} occurrences")
        
        # Check type hints separately
        functions = re.findall(r'def\s+\w+\([^)]*\)', content)
        type_hints = re.findall(r'def\s+\w+\([^)]*:\s*\w+', content)
        if functions and (len(type_hints) / len(functions)) < 0.3:
            penalties += 0.1
            results['red_flags'].append("Missing type hints (<30% coverage)")
        
        # 2. DETECT BEST PRACTICES (bonuses)
        bonuses = 0
        for practice_name, regex in self.best_practices.items():
            matches = re.findall(regex, content, re.MULTILINE)
            if matches:
                bonuses += len(matches) * 0.03  # 3% per occurrence
                results['green_flags'].append(f"{practice_name}: {len(matches)} uses")
        
        # 3. DETECT ALGORITHM SOPHISTICATION
        sophistication_score = 0
        for category, patterns in self.advanced_algorithms.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    sophistication_score += 1
                    results['green_flags'].append(f"Advanced: {category}")
                    break  # Only count category once
        
        # Sophistication levels
        if sophistication_score >= 3:
            results['sophistication_level'] = 'advanced'
            bonuses += 0.3
        elif sophistication_score >= 1:
            results['sophistication_level'] = 'intermediate'
            bonuses += 0.1
        
        # 4. CALCULATE FINAL QUALITY SCORE
        net_adjustment = bonuses - penalties
        results['quality_score'] = max(0.5, min(2.0, 1.0 + net_adjustment))
        
        # Generate reasoning
        if results['quality_score'] > 1.2:
            results['reasoning'].append("High-quality code with best practices")
        elif results['quality_score'] < 0.8:
            results['reasoning'].append("Code quality concerns detected")
        
        return results
    
    def analyze_repository(self, repo_path: str, sample_files: List[str]) -> Dict:
        """
        Analyze a sample of files to get repository-wide quality metrics
        """
        
        total_quality = 0
        all_red_flags = []
        all_green_flags = []
        sophistication_counts = {'basic': 0, 'intermediate': 0, 'advanced': 0}
        
        for file_path in sample_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                analysis = self.analyze_code_quality(content, file_path)
                
                total_quality += analysis['quality_score']
                all_red_flags.extend(analysis['red_flags'])
                all_green_flags.extend(analysis['green_flags'])
                sophistication_counts[analysis['sophistication_level']] += 1
                
            except Exception as e:
                continue
        
        avg_quality = total_quality / len(sample_files) if sample_files else 1.0
        
        # Determine dominant sophistication
        dominant_sophistication = max(sophistication_counts, key=sophistication_counts.get)
        
        return {
            'average_quality_multiplier': round(avg_quality, 2),
            'red_flags_count': len(all_red_flags),
            'green_flags_count': len(all_green_flags),
            'sophistication': dominant_sophistication,
            'sample_size': len(sample_files),
            'red_flags': all_red_flags[:10],  # Top 10
            'green_flags': all_green_flags[:10],
        }


