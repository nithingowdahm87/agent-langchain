"""
Parallel LLM Writer Execution — Run 3 writers concurrently.

Usage:
    from src.utils.parallel import run_writers_parallel

    drafts = run_writers_parallel(
        writers=[(wa, "Gemini"), (wb, "Groq"), (wc, "NVIDIA")],
        generate_fn=lambda writer, ctx: writer.generate(ctx),
        context=ctx_str,
        stage="Docker",
    )
"""

import asyncio
import time
import logging

logger = logging.getLogger("devops-agent.parallel")


def run_writers_parallel(
    writers: list[tuple],
    generate_fn,
    context: str,
    stage: str = "unknown",
    timeout: int = 120,
) -> list[str]:
    """
    Run multiple LLM writers in parallel using asyncio threads.

    Args:
        writers: List of (writer_instance, model_name) tuples
        generate_fn: Function(writer, context) -> str that calls the writer
        context: Context string to pass to each writer
        stage: Pipeline stage name for logging
        timeout: Maximum seconds to wait for all writers

    Returns:
        List of draft strings (empty string on failure)
    """

    async def _run_all():
        tasks = []
        for writer, model_name in writers:
            tasks.append(
                _run_single(writer, model_name, generate_fn, context, stage)
            )
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_single(writer, model_name, fn, ctx, stg):
        start = time.time()
        try:
            result = await asyncio.to_thread(fn, writer, ctx)
            elapsed = time.time() - start
            logger.info(
                "Writer completed | model=%s | stage=%s | latency=%.2fs",
                model_name, stg, elapsed,
                extra={"model": model_name, "stage": stg, "latency": round(elapsed, 2)},
            )
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.warning(
                "Writer failed | model=%s | stage=%s | latency=%.2fs | error=%s: %s",
                model_name, stg, elapsed, type(e).__name__, str(e)[:200],
                extra={"model": model_name, "stage": stg, "latency": round(elapsed, 2), "error_type": type(e).__name__},
            )
            return ""

    # Run the event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're already in an async context — use nest_asyncio or run sync
        results = []
        for writer, model_name in writers:
            start = time.time()
            try:
                result = generate_fn(writer, context)
                elapsed = time.time() - start
                logger.info(
                    "Writer completed (sync fallback) | model=%s | stage=%s | latency=%.2fs",
                    model_name, stage, elapsed,
                )
                results.append(result)
            except Exception as e:
                logger.warning("Writer failed (sync fallback) | model=%s | error=%s", model_name, e)
                results.append("")
        return results
    else:
        raw_results = asyncio.run(_run_all())

    # Convert exceptions to empty strings
    drafts = []
    for r in raw_results:
        if isinstance(r, Exception):
            drafts.append("")
        else:
            drafts.append(r if r else "")

    # Pad to 3 if needed
    while len(drafts) < 3:
        drafts.append("")

    return drafts
