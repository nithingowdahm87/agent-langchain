from dataclasses import dataclass

@dataclass
class DecisionResult:
    """
    Outcome of the Confidence Engine.
    Determines the next step in the pipeline.
    """
    confidence_score: float         # 0.0 to 100.0
    action: str                     # auto_pr | review_pr | draft_pr | manual_review
    reason: str                     # Explanation for the decision
    requires_human_gate: bool = True # Can be set to False for high confidence if allowed
