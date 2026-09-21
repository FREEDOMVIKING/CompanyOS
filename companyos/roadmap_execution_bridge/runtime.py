"""Reliable, observable in-process execution bridge.

The bridge keeps orchestration concerns separate from the supplied execution
handler. It provides idempotent submission, bounded retries, and an inspectable
health snapshot without changing approval or deployment controls.
"""
from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from threading import RLock
from time import time
from typing import Any, Callable, Deque, Dict, Optional


Handler = Callable[[Dict[str, Any]], Any]


@dataclass
class WorkItem:
    key: str
    payload: Dict[str, Any]
    max_attempts: int = 3
    attempts: int = 0
    status: str = "queued"
    last_error: Optional[str] = None
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)


class ExecutionBridge:
    """Small durable-in-memory boundary for reliable execution dispatch."""

    def __init__(self, handler: Optional[Handler] = None, event_limit: int = 200) -> None:
        self._handler = handler
        self._items: "OrderedDict[str, WorkItem]" = OrderedDict()
        self._queue: Deque[str] = deque()
        self._events: Deque[Dict[str, Any]] = deque(maxlen=max(10, event_limit))
        self._lock = RLock()
        self._last_error: Optional[str] = None

    def set_handler(self, handler: Handler) -> None:
        if not callable(handler):
            raise TypeError("handler must be callable")
        with self._lock:
            self._handler = handler
            self._record("handler_ready")

    def submit(self, key: str, payload: Dict[str, Any], max_attempts: int = 3) -> WorkItem:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("key must be a non-empty string")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        if not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        with self._lock:
            existing = self._items.get(key)
            if existing is not None:
                return existing
            item = WorkItem(key=key, payload=dict(payload), max_attempts=max_attempts)
            self._items[key] = item
            self._queue.append(key)
            self._record("submitted", key=key)
            return item

    def run_once(self) -> Optional[WorkItem]:
        with self._lock:
            if not self._queue:
                return None
            key = self._queue.popleft()
            item = self._items[key]
            item.status = "running"
            item.attempts += 1
            item.updated_at = time()
            handler = self._handler
            self._record("started", key=key, attempt=item.attempts)
        try:
            if handler is None:
                raise RuntimeError("execution handler is not configured")
            handler(dict(item.payload))
        except Exception as exc:  # handler failures are data, not worker crashes
            with self._lock:
                item.last_error = f"{type(exc).__name__}: {exc}"
                item.updated_at = time()
                self._last_error = item.last_error
                if item.attempts < item.max_attempts:
                    item.status = "queued"
                    self._queue.append(key)
                    self._record("retry_scheduled", key=key, attempt=item.attempts)
                else:
                    item.status = "failed"
                    self._record("failed", key=key, error=item.last_error)
            return item
        with self._lock:
            item.status = "completed"
            item.updated_at = time()
            self._record("completed", key=key)
            return item

    def health(self) -> Dict[str, Any]:
        with self._lock:
            counts = {state: 0 for state in ("queued", "running", "completed", "failed")}
            for item in self._items.values():
                counts[item.status] = counts.get(item.status, 0) + 1
            return {
                "ready": self._handler is not None,
                "queued": len(self._queue),
                "items": counts,
                "last_error": self._last_error,
                "recent_events": list(self._events),
            }

    def _record(self, event: str, **fields: Any) -> None:
        self._events.append({"event": event, "at": time(), **fields})


__all__ = ["ExecutionBridge", "Handler", "WorkItem"]
