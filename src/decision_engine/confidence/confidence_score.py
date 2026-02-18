from src.decision_engine.contracts.infra_spec import InfraSpec

def compute_confidence(spec: InfraSpec, repair_attempts: int, model_agreement_score: float = 0.0) -> float:
    """
    Calculate confidence score (0-100) based on metrics.
    
    Args:
        spec: The chosen infrastructure specification
        repair_attempts: How many times did we have to fix it? (0 is best)
        model_agreement_score: Did likely models generate similar output? (Advanced)
    """
    base = 0.0
    
    # Weigh security heavily
    base += spec.security_score * 0.4
    
    # Best practices
    base += spec.best_practice_score * 0.3
    
    # Penalize repairs
    # If we had to repair 3 times, we are less confident
    repair_penalty = repair_attempts * 10
    
    # Boost for model agreement (placeholder for now)
    agreement_bonus = model_agreement_score * 20
    
    final = base + agreement_bonus - repair_penalty
    return max(0.0, min(100.0, final))
