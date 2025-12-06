"""
Integration layer for running proposals through the research pipeline.

Responsibilities:
- Centralized, fail-open call to research_pipeline.process_proposal
- Timeout and optional async execution
- Structured logging + lightweight metrics hooks
"""
import copy
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Configuration (env driven)
PIPELINE_ENABLED = os.getenv("RESEARCH_PIPELINE_ENABLED", "true").lower() == "true"
PIPELINE_TIMEOUT = float(os.getenv("RESEARCH_PIPELINE_TIMEOUT", "2.0"))
PIPELINE_ASYNC = os.getenv("RESEARCH_PIPELINE_ASYNC", "false").lower() == "true"
PIPELINE_TEST_MODE = os.getenv("RESEARCH_PIPELINE_TEST_MODE", "true").lower() == "true"

# Reserved metadata bucket to avoid field collisions
RESEARCH_METADATA_KEY = "_research"
RESEARCH_PIPELINE_TAG = "research_pipeline_v1"

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="research-pipeline")

try:
    from research_pipeline import process_proposal as _pipeline_process  # type: ignore
    _pipeline_import_error: Optional[Exception] = None
except Exception as exc:  # pragma: no cover - defensive import guard
    _pipeline_process = None
    _pipeline_import_error = exc


def _record_metric(event: str, duration: Optional[float] = None) -> None:
    """
    Lightweight metric hook. Currently logs; can be wired to real metrics sink later.
    """
    logger.info(
        "research_pipeline.metric",
        extra={
            "metric": "research_pipeline",
            "event": event,
            "duration_ms": round(duration * 1000, 2) if duration is not None else None,
        },
    )


def run_research_pipeline(proposal: Dict[str, Any], source: str = "unknown") -> Dict[str, Any]:
    """
    Safely run a proposal payload through the research pipeline.

    - Fail-open on any error/timeout/import failure
    - Idempotent: if pipeline is disabled or unavailable, returns original payload
    - Adds results under reserved metadata key to avoid UI-visible changes
    """
    if not PIPELINE_ENABLED:
        return proposal

    if _pipeline_process is None:
        logger.debug(
            "research_pipeline unavailable; skipping",
            extra={"source": source, "error": str(_pipeline_import_error)},
        )
        return proposal

    payload = copy.deepcopy(proposal)
    start_time = time.perf_counter()

    def _invoke():
        return _pipeline_process(payload, test_mode=PIPELINE_TEST_MODE)  # type: ignore[arg-type]

    future = _executor.submit(_invoke)

    if PIPELINE_ASYNC:
        # Fire-and-forget; log outcome when done
        def _finish_callback(fut):
            duration = time.perf_counter() - start_time
            if fut.cancelled():
                logger.warning(
                    "research_pipeline async future cancelled", extra={"source": source, "duration_ms": round(duration * 1000, 2)}
                )
                _record_metric("cancelled", duration)
                return
            try:
                fut.result()
                logger.info(
                    "research_pipeline async success",
                    extra={"source": source, "duration_ms": round(duration * 1000, 2)},
                )
                _record_metric("success_async", duration)
            except Exception as exc:  # pragma: no cover - logging only
                logger.warning(
                    "research_pipeline async failed (ignored)",
                    extra={"source": source, "error": str(exc), "duration_ms": round(duration * 1000, 2)},
                )
                _record_metric("failure_async", duration)

        future.add_done_callback(_finish_callback)
        return proposal

    try:
        processed = future.result(timeout=PIPELINE_TIMEOUT)
        duration = time.perf_counter() - start_time
        logger.info(
            "research_pipeline success",
            extra={"source": source, "duration_ms": round(duration * 1000, 2), "tag": RESEARCH_PIPELINE_TAG},
        )
        _record_metric("success", duration)
        return processed or proposal
    except TimeoutError:
        duration = time.perf_counter() - start_time
        logger.warning(
            "research_pipeline timeout; continuing without pipeline",
            extra={"source": source, "timeout_s": PIPELINE_TIMEOUT, "duration_ms": round(duration * 1000, 2)},
        )
        _record_metric("timeout", duration)
        return proposal
    except Exception as exc:
        duration = time.perf_counter() - start_time
        logger.warning(
            "research_pipeline failed; proceeding with original proposal",
            extra={"source": source, "error": str(exc), "duration_ms": round(duration * 1000, 2)},
        )
        _record_metric("failure", duration)
        return proposal


