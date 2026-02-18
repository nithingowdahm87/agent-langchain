from src.decision_engine.contracts.decision_result import DecisionResult

def decide_action(confidence: float) -> DecisionResult:
    """
    Determine the recommended action based on confidence score.
    """
    if confidence >= 90:
        return DecisionResult(
            confidence_score=confidence,
            action="recommend_auto_approve",
            reason="High confidence: Secure, compliant, and robust.",
            requires_human_gate=False 
        )
    elif confidence >= 70:
        return DecisionResult(
            confidence_score=confidence,
            action="recommend_review",
            reason="Good confidence, but standard review recommended.",
            requires_human_gate=True
        )
    elif confidence >= 40:
        return DecisionResult(
            confidence_score=confidence,
            action="recommend_draft",
            reason="Low confidence: Requires careful review.",
            requires_human_gate=True
        )
    else:
        return DecisionResult(
            confidence_score=confidence,
            action="manual_intervention",
            reason="Very low confidence: Significant issues detected.",
            requires_human_gate=True
        )
