from __future__ import annotations
import concurrent.futures
import os
import time
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class BoundedExecutionResult:
    ok: bool
    value: Any = None
    error: str | None = None
    timed_out: bool = False
    elapsed_seconds: float = 0.0

def run_bounded(fn: Callable[[], Any], timeout_seconds: float | None = None) -> BoundedExecutionResult:
    timeout = float(timeout_seconds or os.getenv("COMPANYOS_TASK_TIMEOUT_SECONDS", "90"))
    started = time.monotonic()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="companyos-task")
    fut = pool.submit(fn)
    try:
        value = fut.result(timeout=timeout)
        return BoundedExecutionResult(True, value=value, elapsed_seconds=time.monotonic()-started)
    except concurrent.futures.TimeoutError:
        fut.cancel()
        # Do not wait for a stuck worker during shutdown.
        pool.shutdown(wait=False, cancel_futures=True)
        return BoundedExecutionResult(False, error=f"task_timeout_after_{timeout:g}s",
                                      timed_out=True, elapsed_seconds=time.monotonic()-started)
    except Exception as exc:
        return BoundedExecutionResult(False, error=f"{type(exc).__name__}: {exc}",
                                      elapsed_seconds=time.monotonic()-started)
    finally:
        if fut.done():
            pool.shutdown(wait=False, cancel_futures=True)
