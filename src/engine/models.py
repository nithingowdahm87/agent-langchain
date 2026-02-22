from dataclasses import dataclass
from typing import List

@dataclass
class GeneratedFile:
    path: str
    content: str
    
@dataclass
class ValidationResult:
    passed: bool
    errors: List[str]
