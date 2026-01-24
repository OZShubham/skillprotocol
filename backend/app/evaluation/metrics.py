# backend/app/evaluation/metrics.py
import json
from typing import Dict, Any
from opik.evaluation.metrics import BaseMetric, score_result

class SfiaLevelAccuracy(BaseMetric):
    """
    PRIMARY METRIC: Did we assign the correct SFIA level?
    """
    def __init__(self, name: str = "sfia_accuracy", model=None):
        # We accept 'model' arg to be compatible with Opik instantiation in runner.py
        self.name = name

    def score(self, dataset_item: Dict[str, Any], llm_output: Dict[str, Any], **kwargs) -> score_result.ScoreResult:
        try:
            # 1. Safe extraction of predicted level
            sfia_result = llm_output.get("sfia_result")
            if not sfia_result:
                # Fallback: check if 'predicted' key exists (common in eval traces)
                sfia_result = llm_output.get("predicted") or {}

            predicted = sfia_result.get("sfia_level", 0)
            
            if predicted == 0:
                return score_result.ScoreResult(
                    name=self.name,
                    value=0.0,
                    reason="No SFIA level predicted"
                )
            
            # 2. Comparison
            expected = int(dataset_item.get("expected_sfia_level", 0))
            predicted = int(predicted)
            diff = abs(predicted - expected)
            
            if diff == 0:
                return score_result.ScoreResult(name=self.name, value=1.0, reason=f"✓ Perfect match: {predicted}")
            elif diff == 1:
                return score_result.ScoreResult(name=self.name, value=0.5, reason=f"~ Close match: {predicted} vs {expected}")
            else:
                return score_result.ScoreResult(name=self.name, value=0.0, reason=f"✗ Mismatch: {predicted} vs {expected}")
        
        except Exception as e:
            return score_result.ScoreResult(name=self.name, value=0.0, reason=f"Error: {str(e)}")

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