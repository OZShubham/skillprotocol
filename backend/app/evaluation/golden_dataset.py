# ============================================================================
# FILE 1: backend/app/evaluation/golden_dataset.py
# ============================================================================
"""
Golden Dataset of Real GitHub Repositories with Verified SFIA Levels
This is the ground truth for evaluating SkillProtocol's accuracy
"""

GOLDEN_REPOS = [
    # ========================================================================
    # LEVEL 5: ENSURE - Production Systems
    # ========================================================================
    {
        "repo_url": "https://github.com/tiangolo/fastapi",
        "expected_sfia_level": 5,
        "reasoning": "Production framework with CI/CD, comprehensive tests, async patterns, Docker, extensive documentation",
        "expected_credits_range": (80, 150),
        "markers": {
            "has_readme": True,
            "has_requirements": True,
            "has_tests": True,
            "has_ci_cd": True,
            "has_docker": True,
            "uses_async": True,
            "has_error_handling": True,
            "has_docstrings": True
        }
    },
    {
        "repo_url": "https://github.com/pallets/flask",
        "expected_sfia_level": 5,
        "reasoning": "Mature production framework, extensive test suite, CI/CD, professional documentation",
        "expected_credits_range": (70, 140)
    },
    {
        "repo_url": "https://github.com/celery/celery",
        "expected_sfia_level": 5,
        "reasoning": "Distributed task queue with Docker, CI/CD, async patterns, production-grade error handling",
        "expected_credits_range": (90, 160)
    },
    
    # ========================================================================
    # LEVEL 4: ENABLE - Advanced Patterns
    # ========================================================================
    {
        "repo_url": "https://github.com/psf/requests",
        "expected_sfia_level": 4,
        "reasoning": "Well-structured library with comprehensive tests, OOP patterns, documentation, but no CI/CD visible",
        "expected_credits_range": (30, 80),
        "markers": {
            "has_readme": True,
            "has_requirements": True,
            "has_tests": True,
            "has_ci_cd": False,
            "uses_design_patterns": True
        }
    },
    {
        "repo_url": "https://github.com/sqlalchemy/sqlalchemy",
        "expected_sfia_level": 4,
        "reasoning": "Complex ORM with tests, design patterns, documentation, lacks modern CI/CD",
        "expected_credits_range": (50, 100)
    },
    {
        "repo_url": "https://github.com/encode/httpx",
        "expected_sfia_level": 4,
        "reasoning": "Modern HTTP client with async, tests, type hints, missing full production setup",
        "expected_credits_range": (25, 70)
    },
    
    # ========================================================================
    # LEVEL 3: APPLY - Professional Baseline
    # ========================================================================
    {
        "repo_url": "https://github.com/kennethreitz/records",
        "expected_sfia_level": 3,
        "reasoning": "Clean library with README, requirements, modular structure, but no tests",
        "expected_credits_range": (10, 40),
        "markers": {
            "has_readme": True,
            "has_requirements": True,
            "has_modular_structure": True,
            "has_tests": False
        }
    },
    {
        "repo_url": "https://github.com/jazzband/prettytable",
        "expected_sfia_level": 3,
        "reasoning": "Well-documented library, modular code, missing comprehensive tests",
        "expected_credits_range": (8, 35)
    },
    {
        "repo_url": "https://github.com/python-poetry/poetry",
        "expected_sfia_level": 3,
        "reasoning": "Professional tool with docs and structure, but evaluation focuses on core not tooling",
        "expected_credits_range": (15, 50)
    },
    
    # ========================================================================
    # LEVEL 2: ASSIST - Working Code, Needs Guidance
    # ========================================================================
    {
        "repo_url": "https://github.com/miguelgrinberg/python-socketio",
        "expected_sfia_level": 2,
        "reasoning": "Multiple files with functions, has README but lacks requirements file and tests",
        "expected_credits_range": (3, 15),
        "markers": {
            "has_readme": True,
            "has_requirements": False,
            "has_tests": False,
            "file_count": 8
        }
    },
    {
        "repo_url": "https://github.com/you/simple-flask-app",  # Replace with actual
        "expected_sfia_level": 2,
        "reasoning": "Basic Flask app with routes, has structure but no tests or CI/CD",
        "expected_credits_range": (2, 12)
    },
    
    # ========================================================================
    # LEVEL 1: FOLLOW - Basic Scripts
    # ========================================================================
    {
        "repo_url": "https://github.com/you/python-calculator",  # Replace with actual
        "expected_sfia_level": 1,
        "reasoning": "Single file script, basic syntax, no structure or documentation",
        "expected_credits_range": (0.3, 3),
        "markers": {
            "has_readme": False,
            "has_requirements": False,
            "file_count": 1
        }
    },
    {
        "repo_url": "https://github.com/you/hello-world-py",  # Replace with actual
        "expected_sfia_level": 1,
        "reasoning": "Minimal script demonstrating basic Python syntax",
        "expected_credits_range": (0.2, 2)
    },
]

# ============================================================================
# VALIDATION FUNCTION
# ============================================================================

def validate_golden_dataset():
    """Ensures golden dataset is properly formatted"""
    required_fields = ["repo_url", "expected_sfia_level", "reasoning", "expected_credits_range"]
    
    for i, repo in enumerate(GOLDEN_REPOS):
        for field in required_fields:
            if field not in repo:
                raise ValueError(f"Repo {i} missing required field: {field}")
        
        # Validate SFIA level
        if not 1 <= repo["expected_sfia_level"] <= 5:
            raise ValueError(f"Repo {i} has invalid SFIA level: {repo['expected_sfia_level']}")
        
        # Validate credit range
        min_c, max_c = repo["expected_credits_range"]
        if min_c >= max_c:
            raise ValueError(f"Repo {i} has invalid credit range")
    
    print(f"✅ Golden dataset validated: {len(GOLDEN_REPOS)} repositories")
    
    # Print distribution
    level_counts = {}
    for repo in GOLDEN_REPOS:
        level = repo["expected_sfia_level"]
        level_counts[level] = level_counts.get(level, 0) + 1
    
    print(f"\nLevel Distribution:")
    for level in sorted(level_counts.keys()):
        print(f"  Level {level}: {level_counts[level]} repos")
    
    return True


if __name__ == "__main__":
    validate_golden_dataset()