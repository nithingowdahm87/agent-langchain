from typing import Callable, Any, Tuple
from src.decision_engine.contracts.infra_spec import InfraSpec

class RepairAgent:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        
    def repair_until_valid(
        self, 
        content: str, 
        validator_fn: Callable[[str], Tuple[bool, str]], 
        fixer_fn: Callable[[str, str], str]
    ) -> str:
        """
        Generic repair loop.
        
        Args:
            content: The artifact content (YAML/Dockerfile/etc)
            validator_fn: Function returning (is_valid, error_msg)
            fixer_fn: Function taking (content, error_msg) and returning fixed content
        """
        current_content = content
        
        for attempt in range(self.max_retries):
            is_valid, error = validator_fn(current_content)
            if is_valid:
                return current_content
                
            # Attempt fix
            try:
                current_content = fixer_fn(current_content, error)
            except Exception as e:
                # If fixer fails, return last known state or raise?
                # For now, break and return invalid content (will be caught downstream)
                break
                
        return current_content
