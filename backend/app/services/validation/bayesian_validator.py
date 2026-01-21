"""
Bayesian SFIA Validator
Provides statistical confidence bounds for LLM-based assessments
"""

import math
from typing import Dict, Any, List

# ============================================================================
# BAYESIAN MODEL PARAMETERS
# ============================================================================

SFIA_LEVELS = [1, 2, 3, 4, 5]

# Conservative priors (based on typical GitHub distribution)
PRIORS = {
    1: 0.15,  # Beginner scripts
    2: 0.30,  # Working code, needs structure
    3: 0.30,  # Professional baseline
    4: 0.20,  # Advanced patterns
    5: 0.05,  # Production systems
}

# Maintainability Index likelihoods per level
MI_MEANS = {
    1: 45.0,  # Low maintainability
    2: 55.0,
    3: 65.0,  # Average
    4: 75.0,
    5: 85.0,  # High maintainability
}
MI_STD = 12.0

# Git stability likelihoods per level
GIT_STABILITY_MEANS = {
    1: 0.30,  # Unstable/new
    2: 0.45,
    3: 0.60,  # Moderate
    4: 0.75,
    5: 0.85,  # Very stable
}
GIT_STD = 0.15

# Test presence probability per level
TEST_PROBABILITIES = {
    1: 0.05,  # Rarely have tests
    2: 0.15,
    3: 0.30,
    4: 0.70,  # Usually have tests
    5: 0.90,  # Almost always
}

# Complexity density likelihoods (complexity/SLOC)
COMPLEXITY_MEANS = {
    1: 0.05,  # Very simple
    2: 0.10,
    3: 0.15,  # Moderate
    4: 0.25,
    5: 0.35,  # Complex algorithms
}
COMPLEXITY_STD = 0.08


# ============================================================================
# LIKELIHOOD FUNCTIONS
# ============================================================================

def log_gaussian(x: float, mean: float, std: float) -> float:
    """Log probability of Gaussian distribution"""
    if std == 0:
        return 0.0
    return -math.log(std * math.sqrt(2 * math.pi)) - ((x - mean) ** 2 / (2 * std ** 2))


def log_bernoulli(observed: bool, p: float) -> float:
    """Log probability of Bernoulli distribution"""
    # Clamp probability to avoid log(0)
    p = max(0.01, min(0.99, p))
    return math.log(p if observed else (1 - p))


# ============================================================================
# BAYESIAN INFERENCE
# ============================================================================

class BayesianSFIAValidator:
    """
    Validates LLM SFIA assessments using Bayesian inference
    """
    
    def get_statistical_suggestion(self, metrics: Dict[str, Any], git_stability: float = 0.5) -> Dict[str, Any]:
        """
        Get the statistical prior BEFORE calling the LLM.
        This allows us to 'anchor' the LLM with hard data.
        """
        # Calculate probabilities based solely on metrics
        probabilities = self._infer_level_distribution(metrics, git_stability)
        
        # Find the most likely level
        best_level = max(probabilities, key=probabilities.get)
        confidence = probabilities[best_level]
        
        # Get plausible range (any level with > 15% probability)
        plausible_range = sorted([lvl for lvl, p in probabilities.items() if p > 0.15])
        
        return {
            "suggested_level": best_level,
            "confidence": confidence,
            "distribution": probabilities,
            "plausible_range": plausible_range,
            "metrics_used": {
                "maintainability_index": metrics.get("ncrf", {}).get("avg_mi"),
                "sloc": metrics.get("ncrf", {}).get("total_sloc")
            }
        }

    def validate_assessment(
        self,
        predicted_level: int,
        metrics: Dict[str, Any],
        git_stability: float = 0.5
    ) -> Dict[str, Any]:
        """
        Main validation function (Post-Check)
        """
        
        # Calculate posterior probabilities
        probabilities = self._infer_level_distribution(metrics, git_stability)
        
        # Confidence in predicted level
        confidence = probabilities.get(predicted_level, 0.0)
        
        # Expected range (levels with P > 15%)
        expected_range = sorted([
            lvl for lvl, prob in probabilities.items() 
            if prob > 0.15
        ])
        
        # Most likely level from Bayesian model
        bayesian_best = max(probabilities, key=probabilities.get)
        
        # Alert if discrepancy
        alert = confidence < 0.25 or abs(predicted_level - bayesian_best) > 1
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            predicted_level, 
            bayesian_best, 
            confidence, 
            expected_range
        )
        
        return {
            "confidence": round(confidence, 3),
            "probability_distribution": {k: round(v, 3) for k, v in probabilities.items()},
            "expected_range": expected_range,
            "bayesian_best_estimate": bayesian_best,
            "alert": alert,
            "reasoning": reasoning
        }
    
    def _infer_level_distribution(
        self,
        metrics: Dict[str, Any],
        git_stability: float
    ) -> Dict[int, float]:
        """
        Bayesian inference: P(Level | Evidence)
        """
        
        # Extract evidence
        avg_mi = metrics.get("ncrf", {}).get("avg_mi", 65.0)
        complexity_density = metrics.get("ncrf", {}).get("complexity_density", 0.15)
        has_tests = metrics.get("markers", {}).get("has_tests", False)
        
        log_posteriors = {}
        
        for level in SFIA_LEVELS:
            # Start with prior
            log_p = math.log(PRIORS[level])
            
            # Likelihood: Maintainability Index
            log_p += log_gaussian(avg_mi, MI_MEANS[level], MI_STD)
            
            # Likelihood: Complexity density
            log_p += log_gaussian(complexity_density, COMPLEXITY_MEANS[level], COMPLEXITY_STD)
            
            # Likelihood: Test presence
            log_p += log_bernoulli(has_tests, TEST_PROBABILITIES[level])
            
            # Likelihood: Git stability
            if git_stability > 0:
                log_p += log_gaussian(git_stability, GIT_STABILITY_MEANS[level], GIT_STD)
            
            log_posteriors[level] = log_p
        
        # Convert log probabilities to normalized probabilities
        # Use log-sum-exp trick for numerical stability
        max_log = max(log_posteriors.values())
        exp_probs = {
            lvl: math.exp(lp - max_log) 
            for lvl, lp in log_posteriors.items()
        }
        
        total = sum(exp_probs.values())
        
        return {
            lvl: prob / total 
            for lvl, prob in exp_probs.items()
        }
    
    def _generate_reasoning(
        self,
        predicted: int,
        bayesian_best: int,
        confidence: float,
        expected_range: List[int]
    ) -> str:
        """Generate human-readable reasoning"""
        
        if confidence >= 0.7:
            return f"High confidence: Bayesian model strongly supports Level {predicted}"
        
        elif confidence >= 0.4:
            if predicted == bayesian_best:
                return f"Moderate confidence: Level {predicted} is plausible (range: {expected_range})"
            else:
                return f"Moderate confidence: Level {predicted} predicted, but Bayesian suggests Level {bayesian_best}"
        
        else:
            return f"Low confidence: Large uncertainty. Bayesian suggests Level {bayesian_best}, but range is {expected_range}"


# ============================================================================
# HELPER: Calculate Maintainability Index
# ============================================================================

def calculate_maintainability_index(metrics: Dict[str, Any]) -> float:
    """
    Calculate MI from scan metrics
    MI = 171 - 5.2*ln(V) - 0.23*G - 16.2*ln(L)
    
    Simplified version using SLOC and complexity
    """
    
    ncrf = metrics.get("ncrf", {})
    total_sloc = ncrf.get("total_sloc", 100)
    total_complexity = ncrf.get("total_complexity", 10)
    
    if total_sloc == 0:
        return 65.0  # Neutral
    
    # Simplified MI formula
    raw_mi = (
        171
        - 5.2 * math.log(max(1, total_complexity))
        - 0.23 * 15  # Average cyclomatic complexity
        - 16.2 * math.log(total_sloc)
    )
    
    # Normalize to 0-100 scale
    normalized = max(0.0, min(100.0, raw_mi * 100 / 171))
    
    return round(normalized, 2)


# ============================================================================
# SINGLETON
# ============================================================================

_validator_instance = None

def get_validator() -> BayesianSFIAValidator:
    """Get singleton validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = BayesianSFIAValidator()
    return _validator_instance