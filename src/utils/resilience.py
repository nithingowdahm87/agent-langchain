"""
Resilience utilities — Retry with exponential backoff for LLM calls.

Usage:
    from src.utils.resilience import safe_llm_call

    result = safe_llm_call(client.call, prompt, model_name="gemini")
"""

import time
import logging

logger = logging.getLogger("devops-agent.resilience")

# ─── Configuration ──────────────────────────────────────────────────

MAX_RETRIES = 3
BACKOFF_BASE = 2       # seconds
BACKOFF_MAX = 10       # seconds
BACKOFF_MULTIPLIER = 2

# Transient errors worth retrying
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


# ─── Retry Logic ────────────────────────────────────────────────────

def safe_llm_call(
    callable_fn,
    prompt: str,
    model_name: str = "unknown",
    stage: str = "unknown",
    max_retries: int = MAX_RETRIES,
) -> str:
    """
    Call an LLM with retry + exponential backoff.

    Args:
        callable_fn: The function to call (e.g., client.call)
        prompt: The prompt string
        model_name: For logging/tracing
        stage: Pipeline stage name for logging
        max_retries: Number of retry attempts

    Returns:
        LLM response string

    Raises:
        RuntimeError: After all retries exhausted
    """
    last_exception = None
    wait_time = BACKOFF_BASE

    for attempt in range(1, max_retries + 1):
        try:
            start = time.time()
            result = callable_fn(prompt)
            elapsed = time.time() - start

            logger.info(
                "LLM call succeeded | model=%s | stage=%s | attempt=%d/%d | latency=%.2fs",
                model_name, stage, attempt, max_retries, elapsed,
            )
            return result

        except Exception as e:
            last_exception = e
            error_type = type(e).__name__

            # Check if it's an HTTP error with a retryable status code
            retryable = True
            status_code = getattr(e, "status_code", None) or getattr(
                getattr(e, "response", None), "status_code", None
            )
            if status_code and status_code not in _RETRYABLE_STATUS_CODES:
                retryable = False

            logger.warning(
                "LLM call failed | model=%s | stage=%s | attempt=%d/%d | error=%s: %s | retryable=%s",
                model_name, stage, attempt, max_retries, error_type, str(e)[:200], retryable,
            )

            if not retryable:
                break

            if attempt < max_retries:
                sleep_duration = min(wait_time, BACKOFF_MAX)
                logger.info("Retrying in %.1fs...", sleep_duration)
                time.sleep(sleep_duration)
                wait_time *= BACKOFF_MULTIPLIER

    raise RuntimeError(
        f"LLM call failed after {max_retries} attempts | "
        f"model={model_name} | stage={stage} | "
        f"last_error={type(last_exception).__name__}: {last_exception}"
    )
