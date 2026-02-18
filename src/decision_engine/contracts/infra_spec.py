from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class InfraSpec:
    """
    Structured output from a Writer agent.
    Contains the raw file content plus metadata for scoring.
    """
    file_content: str               # The actual generated code (YAML/Dockerfile/etc)
    model_name: str                 # Which model generated this? (Gemini/Groq/NVIDIA)
    
    # Scoring Metrics (0-100) populated by the Reviewer/Scorer or self-reported
    security_score: int = 0
    best_practice_score: int = 0
    complexity_score: int = 0       # Lower is better usually, or balanced
    performance_score: int = 0
    
    # Compliance Details
    violations: List[str] = None    # List of policy violation IDs
    reasoning: str = ""             # Why was this approach chosen?
    
    def __post_init__(self):
        if self.violations is None:
            self.violations = []
