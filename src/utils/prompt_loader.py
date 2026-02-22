import os
import string
from pathlib import Path

def load_prompt(stage: str, role: str) -> str:
    """
    Load prompt template from configs/prompts/
    
    Args:
        stage: dockerfile, kubernetes, cicd, etc.
        role: writer_a_generalist, writer_b_security, etc.
    
    Returns:
        Prompt template string
    
    Raises:
        FileNotFoundError: If prompt file does not exist.
    """
    base_path = Path("configs/prompts")
    prompt_path = base_path / stage / f"{role}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    
    return prompt_path.read_text(encoding="utf-8")

class _SafeDict(dict):
    """Returns the original {key} placeholder for any missing key."""
    def __missing__(self, key):
        return "{" + key + "}"

def render_prompt(template: str, context: dict) -> str:
    """
    Render prompt template with application context.
    Unknown keys (e.g. {APP_VERSION} in Dockerfile code examples) are left intact
    and passed through as-is to the LLM — only known template keys like {context}
    and {plan_summary} are substituted.
    """
    return template.format_map(_SafeDict(context))
