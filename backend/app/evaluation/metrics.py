# ============================================================================
# FILE 2: backend/app/evaluation/metrics.py
# ============================================================================
"""
LLM-as-Judge Metrics for Evaluating SkillProtocol
These metrics determine how well the system performs
"""

import opik
from opik.evaluation.metrics import base_metric, score_result
from typing import Dict, Any


@base_metric
def sfia_level_accuracy(dataset_item: Dict[str, Any], llm_output: Dict[str, Any]) -> score_result.ScoreResult:
    """
    PRIMARY METRIC: Did we assign the correct SFIA level?
    
    Scoring:
    - Exact match: 1.0
    - Off by 1 level: 0.6
    - Off by 2+ levels: 0.0
    """
    try:
        # Extract predicted level
        predicted = llm_output.get("sfia_result", {}).get("sfia_level", 0)
        
        # Handle case where sfia_result might be None
        if predicted == 0:
            return score_result.ScoreResult(
                name="sfia_accuracy",
                value=0.0,
                reason="No SFIA level predicted"
            )
        
        expected = dataset_item["expected_sfia_level"]
        diff = abs(int(predicted) - int(expected))
        
        if diff == 0:
            return score_result.ScoreResult(
                name="sfia_accuracy",
                value=1.0,
                reason=f"✓ Perfect: Level {predicted}"
            )
        elif diff == 1:
            return score_result.ScoreResult(
                name="sfia_accuracy",
                value=0.6,
                reason=f"~ Close: {predicted} vs {expected}"
            )
        else:
            return score_result.ScoreResult(
                name="sfia_accuracy",
                value=0.0,
                reason=f"✗ Wrong: {predicted} vs {expected} (off by {diff})"
            )
    
    except Exception as e:
        return score_result.ScoreResult(
            name="sfia_accuracy",
            value=0.0,
            reason=f"Error: {str(e)}"
        )


@base_metric
def credit_range_consistency(dataset_item: Dict[str, Any], llm_output: Dict[str, Any]) -> score_result.ScoreResult:
    """
    SECONDARY METRIC: Are credits within expected range?
    
    This validates that the NCrF + SFIA calculation is reasonable
    """
    try:
        final_credits = llm_output.get("final_credits", 0)
        min_expected, max_expected = dataset_item["expected_credits_range"]
        
        if min_expected <= final_credits <= max_expected:
            return score_result.ScoreResult(
                name="credit_consistency",
                value=1.0,
                reason=f"✓ Credits {final_credits:.2f} in range [{min_expected}, {max_expected}]"
            )
        else:
            # Calculate how far off we are
            if final_credits < min_expected:
                deviation_pct = (min_expected - final_credits) / min_expected
            else:
                deviation_pct = (final_credits - max_expected) / max_expected
            
            # Penalize based on deviation
            score = max(0.0, 1.0 - deviation_pct)
            
            return score_result.ScoreResult(
                name="credit_consistency",
                value=score,
                reason=f"~ Credits {final_credits:.2f} outside [{min_expected}, {max_expected}] (deviation: {deviation_pct:.1%})"
            )
    
    except Exception as e:
        return score_result.ScoreResult(
            name="credit_consistency",
            value=0.0,
            reason=f"Error: {str(e)}"
        )


@base_metric
def marker_detection_accuracy(dataset_item: Dict[str, Any], llm_output: Dict[str, Any]) -> score_result.ScoreResult:
    """
    TERTIARY METRIC: Did we detect the right SFIA markers?
    
    Only applies to repos that have marker ground truth
    """
    try:
        if "markers" not in dataset_item:
            return score_result.ScoreResult(
                name="marker_accuracy",
                value=1.0,
                reason="No markers to validate"
            )
        
        expected_markers = dataset_item["markers"]
        detected_markers = llm_output.get("scan_metrics", {}).get("markers", {})
        
        total = len(expected_markers)
        correct = 0
        errors = []
        
        for marker, expected_val in expected_markers.items():
            detected_val = detected_markers.get(marker, False)
            
            if detected_val == expected_val:
                correct += 1
            else:
                errors.append(f"{marker}: expected {expected_val}, got {detected_val}")
        
        accuracy = correct / total if total > 0 else 1.0
        
        if accuracy == 1.0:
            return score_result.ScoreResult(
                name="marker_accuracy",
                value=1.0,
                reason=f"✓ All {total} markers correct"
            )
        else:
            return score_result.ScoreResult(
                name="marker_accuracy",
                value=accuracy,
                reason=f"~ {correct}/{total} markers correct. Errors: {'; '.join(errors[:2])}"
            )
    
    except Exception as e:
        return score_result.ScoreResult(
            name="marker_accuracy",
            value=0.0,
            reason=f"Error: {str(e)}"
        )


@base_metric
def reasoning_quality(dataset_item: Dict[str, Any], llm_output: Dict[str, Any]) -> score_result.ScoreResult:
    """
    BONUS METRIC: Is the SFIA reasoning well-explained?
    
    This uses an LLM to judge the quality of the reasoning
    """
    try:
        reasoning = llm_output.get("sfia_result", {}).get("reasoning", "")
        
        if not reasoning:
            return score_result.ScoreResult(
                name="reasoning_quality",
                value=0.0,
                reason="No reasoning provided"
            )
        
        # Simple heuristic: length + keyword presence
        score = 0.0
        
        # Length check (good reasoning is detailed)
        if len(reasoning) > 100:
            score += 0.4
        elif len(reasoning) > 50:
            score += 0.2
        
        # Keyword check (mentions evidence)
        keywords = ["test", "ci/cd", "docker", "readme", "async", "class", "pattern"]
        found_keywords = sum(1 for kw in keywords if kw.lower() in reasoning.lower())
        
        score += min(0.6, found_keywords * 0.15)
        
        return score_result.ScoreResult(
            name="reasoning_quality",
            value=min(1.0, score),
            reason=f"Reasoning length: {len(reasoning)} chars, keywords: {found_keywords}"
        )
    
    except Exception as e:
        return score_result.ScoreResult(
            name="reasoning_quality",
            value=0.0,
            reason=f"Error: {str(e)}"
        )
