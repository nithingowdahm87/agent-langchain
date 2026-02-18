import os
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
    # Base path relative to this file? No, relative to project root.
    # We assume CWD is project root or we find it.
    # Best to rely on relative path from repo root.
    
    base_path = Path("configs/prompts")
    prompt_path = base_path / stage / f"{role}.md"
    
    if not prompt_path.exists():
        # Fallback: try absolute path if running from deep dir? 
        # Actually better to just fail so we catch config errors.
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    
    return prompt_path.read_text(encoding="utf-8")

def render_prompt(template: str, context: dict) -> str:
    """
    Render prompt template with application context.
    Safely formats the string.
    """
    try:
        return template.format(**context)
    except KeyError as e:
        # If a key is missing, we might want to warn or fail
        raise ValueError(f"Missing context key for prompt: {e}")
