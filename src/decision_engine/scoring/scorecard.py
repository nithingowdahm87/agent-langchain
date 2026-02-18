from src.decision_engine.contracts.infra_spec import InfraSpec

def weighted_score(spec: InfraSpec) -> float:
    """
    Compute a deterministic score (0-100) for an infrastructure draft.
    
    Weights:
    - Security: 40% (Most critical)
    - Best Practices: 30%
    - Simplicity: 20% (Inverted Complexity)
    - Performance: 10%
    """
    
    # Invert complexity: 0 complexity = 100 simplicity, 100 complexity = 0 simplicity
    simplicity_score = max(0, 100 - spec.complexity_score)
    
    # Penalty for violations
    # Critical violations should tank the score
    violation_penalty = len(spec.violations) * 15
    
    raw_score = (
        (spec.security_score * 0.4) +
        (spec.best_practice_score * 0.3) +
        (simplicity_score * 0.2) +
        (spec.performance_score * 0.1)
    )
    
    final_score = max(0, raw_score - violation_penalty)
    return round(final_score, 1)
