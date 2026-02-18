from typing import List, Tuple
from src.decision_engine.contracts.infra_spec import InfraSpec
from .scorecard import weighted_score

class Evaluator:
    def evaluate_candidates(self, candidates: List[InfraSpec]) -> Tuple[InfraSpec, float]:
        """
        Select the best candidate from a list of drafts.
        Returns (BestSpec, Score).
        """
        if not candidates:
            raise ValueError("No candidates to evaluate")
            
        scored_candidates = []
        for c in candidates:
            s = weighted_score(c)
            scored_candidates.append((c, s))
            
        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        best = scored_candidates[0]
        return best # (Spec, Score)
