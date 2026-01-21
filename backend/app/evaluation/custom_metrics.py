from typing import Any
from opik.evaluation.metrics import BaseMetric, score_result
from opik.message_processing.emulation.models import SpanModel

class BayesianAlignmentMetric(BaseMetric):
    """
    A custom Task Span Metric that checks if the LLM's final decision
    aligned with the Bayesian Statistics.
    """
    def __init__(self, name: str = "bayesian_alignment"):
        self.name = name

    def score(self, task_span: SpanModel, **ignored_kwargs: Any) -> score_result.ScoreResult:
        # This metric looks at the FINAL trace output
        output = task_span.output or {}
        
        # Extract the relevant data from your trace output structure
        sfia_result = output.get("sfia_result", {})
        val_result = output.get("validation_result", {})
        
        llm_level = sfia_result.get("sfia_level")
        stats_level = val_result.get("bayesian_best_estimate")
        
        if llm_level is None or stats_level is None:
            return score_result.ScoreResult(value=0.0, name=self.name, reason="Missing data")

        # Logic: Did they agree?
        diff = abs(llm_level - stats_level)
        
        if diff == 0:
            return score_result.ScoreResult(value=1.0, name=self.name, reason="Perfect Agreement")
        elif diff == 1:
            return score_result.ScoreResult(value=0.5, name=self.name, reason="Minor Deviation (1 level)")
        else:
            return score_result.ScoreResult(value=0.0, name=self.name, reason=f"Major Deviation: LLM {llm_level} vs Stats {stats_level}")