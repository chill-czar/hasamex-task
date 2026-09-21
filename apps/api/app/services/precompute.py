"""Precomputation service for Hasamex Expert Interview Analyses.

Computes and materializes all 6 interview guide questions, cross-call themes,
and contrasting viewpoints concurrently with rate-limiting semaphore (max 3 concurrent)
to eliminate startup latency and cold-boot penalties.
"""

import asyncio
import logging
import time
from typing import Dict, Any
from apps.api.app.services.analyzer import get_analyzer
from apps.api.app.services.repository import get_repository

logger = logging.getLogger("hasamex.precompute")


async def precompute_all(force_refresh: bool = False, max_concurrency: int = 3) -> Dict[str, Any]:
    """Runs parallel precomputation for any missing or stale analyses."""
    start_time = time.perf_counter()
    analyzer = get_analyzer()
    repo = get_repository()
    sem = asyncio.Semaphore(max_concurrency)

    tasks_to_run = []
    keys_status = {}

    # Check 6 guide questions
    for q_id in range(1, 7):
        key = f"guide_q{q_id}"
        cached = repo.get_materialized_analysis(key)
        if not force_refresh and cached and cached["content_hash"] == analyzer.content_hash:
            keys_status[key] = "cached"
        else:
            keys_status[key] = "pending"

            async def _run_guide(qid=q_id):
                async with sem:
                    logger.info(f"Computing analysis for guide question {qid}...")
                    return await asyncio.to_thread(analyzer.get_guide_question_analysis, qid, force_refresh=True)

            tasks_to_run.append(_run_guide())

    # Check themes
    cached_themes = repo.get_materialized_analysis("themes")
    if not force_refresh and cached_themes and cached_themes["content_hash"] == analyzer.content_hash:
        keys_status["themes"] = "cached"
    else:
        keys_status["themes"] = "pending"

        async def _run_themes():
            async with sem:
                logger.info("Computing common themes across calls...")
                return await asyncio.to_thread(analyzer.get_theme_analyses, force_refresh=True)

        tasks_to_run.append(_run_themes())

    # Check disagreements
    cached_disagreements = repo.get_materialized_analysis("disagreements")
    if not force_refresh and cached_disagreements and cached_disagreements["content_hash"] == analyzer.content_hash:
        keys_status["disagreements"] = "cached"
    else:
        keys_status["disagreements"] = "pending"

        async def _run_disagreements():
            async with sem:
                logger.info("Computing contrasting viewpoints across calls...")
                return await asyncio.to_thread(analyzer.get_disagreement_analyses, force_refresh=True)

        tasks_to_run.append(_run_disagreements())

    if tasks_to_run:
        logger.info(f"Running {len(tasks_to_run)} precomputations with concurrency={max_concurrency}...")
        await asyncio.gather(*tasks_to_run)
    else:
        logger.info("All 8 analyses are already up to date in database.")

    # Warm in-memory cache with freshly persisted data
    analyzer.warm_cache()

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(f"Precomputation completed in {duration_ms:.2f}ms.")

    return {
        "status": "complete",
        "duration_ms": duration_ms,
        "computed_count": len(tasks_to_run),
        "cached_count": len(keys_status) - len(tasks_to_run),
        "keys": keys_status,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    asyncio.run(precompute_all(force_refresh=False))
