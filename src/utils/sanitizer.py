"""
Input Sanitizer — Prevents prompt injection from user feedback.

Usage:
    from src.utils.sanitizer import sanitize_feedback

    safe_text = sanitize_feedback(raw_user_input)
"""

import re
import logging

logger = logging.getLogger("devops-agent.sanitizer")

# ─── Configuration ──────────────────────────────────────────────────

MAX_FEEDBACK_LENGTH = 500

# Characters/patterns that could enable prompt injection or shell escape
_DANGEROUS_PATTERNS = [
    (r'[;|&`$]', ''),                     # Shell metacharacters
    (r'\\[nrtx]', ' '),                    # Escape sequences
    (r'\x00-\x08\x0b\x0c\x0e-\x1f', ''),  # Control characters
]

# Prompt injection markers
_INJECTION_MARKERS = [
    "ignore previous",
    "ignore above",
    "disregard",
    "you are now",
    "system:",
    "assistant:",
    "new instructions",
    "forget everything",
]


# ─── Public API ─────────────────────────────────────────────────────

def sanitize_feedback(text: str, max_length: int = MAX_FEEDBACK_LENGTH) -> str:
    """
    Sanitize user feedback before injecting into LLM prompts.

    - Strips shell metacharacters (; | & ` $)
    - Removes control characters
    - Detects and warns on prompt injection attempts
    - Truncates to max_length

    Args:
        text: Raw user input
        max_length: Maximum allowed character count

    Returns:
        Sanitized string safe for LLM prompt injection
    """
    if not text or not text.strip():
        return ""

    original = text
    cleaned = text.strip()

    # Remove shell metacharacters
    cleaned = re.sub(r'[;|&`$\\]', '', cleaned)

    # Remove control characters (keep newlines and tabs for readability)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)

    # Check for prompt injection patterns
    lower = cleaned.lower()
    for marker in _INJECTION_MARKERS:
        if marker in lower:
            logger.warning(
                "⚠️  Prompt injection attempt detected: '%s' found in feedback",
                marker,
            )
            # Remove the injection marker but keep the rest
            cleaned = re.sub(re.escape(marker), '', cleaned, flags=re.IGNORECASE)

    # Truncate
    if len(cleaned) > max_length:
        logger.warning(
            "Feedback truncated from %d to %d characters",
            len(cleaned), max_length,
        )
        cleaned = cleaned[:max_length] + "..."

    # Log if content was modified
    if cleaned != original.strip():
        logger.info("User feedback sanitized (removed unsafe characters)")

    return cleaned
