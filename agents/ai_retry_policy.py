#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")

def run_with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 2.0,
    max_delay_seconds: float = 30.0,
) -> T:
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            if attempt >= max_attempts:
                break
            delay = min(max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)))
            time.sleep(delay)

    assert last_error is not None
    raise last_error
