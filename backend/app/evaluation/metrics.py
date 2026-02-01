# backend/app/evaluation/metrics.py
import json
from typing import Dict, Any, Optional
from opik.evaluation.metrics import BaseMetric, score_result

class SfiaLevelAccuracy(BaseMetric):
    """
    Checks if the predicted SFIA level matches the expected level.
    """
    def __init__(self, name: str = "sfia_accuracy"):
        super().__init__(name=name)

    def score(self, dataset_item: Dict[str, Any], llm_output: Dict[str, Any] = None, **kwargs) -> score_result.ScoreResult:
        try:
            # Handle cases where input might be direct values or dicts
            expected_val = dataset_item.get("expected_sfia_level") or dataset_item.get("expected_output")
            expected = int(expected_val)
            
            # Extract predicted from the output dictionary or the raw string if needed
            # The 'llm_output' here comes from your evaluation_task return value
            if isinstance(llm_output, dict):
                sfia_result = llm_output.get("sfia_result", {})
                predicted = sfia_result.get("sfia_level", 0)
            else:
                # Fallback if output is raw string
                predicted = 0

            predicted = int(predicted)
            diff = abs(predicted - expected)
            
            if diff == 0:
                return score_result.ScoreResult(name=self.name, value=1.0, reason=f"Perfect match (L{predicted})")
            elif diff == 1:
                return score_result.ScoreResult(name=self.name, value=0.5, reason=f"Close match (Pred: {predicted}, Exp: {expected})")
            else:
                return score_result.ScoreResult(name=self.name, value=0.0, reason=f"Mismatch (Pred: {predicted}, Exp: {expected})")
        
        except Exception as e:
            return score_result.ScoreResult(name=self.name, value=0.0, reason=f"Scoring Error: {str(e)}")
        

class CreditRangeConsistency(BaseMetric):
    """
    SECONDARY METRIC: Are credits within expected range?
    """
    def __init__(self, name: str = "credit_consistency", model=None):
        self.name = name

    def score(self, dataset_item: Dict[str, Any], llm_output: Dict[str, Any], **kwargs) -> score_result.ScoreResult:
        try:
            final_credits = float(llm_output.get("final_credits", 0))
            expected_range = dataset_item.get("expected_credits_range", (0, 0))
            min_exp, max_exp = expected_range
            
            if min_exp <= final_credits <= max_exp:
                return score_result.ScoreResult(name=self.name, value=1.0, reason="Within range")
            
            # Partial credit for being close
            deviation = min(abs(final_credits - min_exp), abs(final_credits - max_exp))
            if deviation < (max_exp - min_exp) * 0.5:
                return score_result.ScoreResult(name=self.name, value=0.5, reason="Slightly out of range")
                
            return score_result.ScoreResult(name=self.name, value=0.0, reason=f"Out of range: {final_credits}")
        except Exception:
            return score_result.ScoreResult(name=self.name, value=0.0, reason="Error calc credits")

# Placeholder classes for other metrics to avoid import errors
class MarkerDetectionAccuracy(BaseMetric):
    def __init__(self, name: str = "marker_accuracy", model=None):
        self.name = name
    def score(self, **kwargs): return score_result.ScoreResult(name=self.name, value=1.0, reason="Not Implemented")

class ReasoningQuality(BaseMetric):
    def __init__(self, name: str = "reasoning_quality", model=None):
        self.name = name
    def score(self, **kwargs): return score_result.ScoreResult(name=self.name, value=1.0, reason="Not Implemented")