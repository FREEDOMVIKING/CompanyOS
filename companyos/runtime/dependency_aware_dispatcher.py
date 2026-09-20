from __future__ import annotations

import os
import time

from companyos.runtime.autonomous_task_dispatcher import (
    AutonomousTaskDispatcher,
    DispatchResult,
)


class DependencyAwareDispatcher:
    """
    Dependency-aware exact dispatcher.

    V28.3 removes the O(window * entire_queue) dependency scan. A completed
    (goal_id, stage) index is built once per bounded batch and updated as
    tasks complete.
    """

    def __init__(self, dispatcher: AutonomousTaskDispatcher) -> None:
        self.dispatcher = dispatcher
        self.queue = dispatcher.queue

    @staticmethod
    def _payload(task):
        return task.payload if isinstance(task.payload, dict) else {}

    def _completed_stage_index(self) -> set[tuple[str, str]]:
        done: set[tuple[str, str]] = set()
        for task in self.queue._iter_task_files():
            if task.state != "COMPLETED":
                continue
            payload = self._payload(task)
            goal_id = payload.get("goal_id")
            stage = payload.get("stage")
            if goal_id and stage:
                done.add((str(goal_id), str(stage)))
        return done

    def _dependency_satisfied_with_index(
        self,
        task,
        completed: set[tuple[str, str]],
    ) -> bool:
        payload = self._payload(task)
        dep = payload.get("depends_on_stage")
        if not dep:
            return True
        goal_id = payload.get("goal_id")
        return bool(goal_id) and (str(goal_id), str(dep)) in completed

    def _window(self, limit: int):
        cursor_path = self.queue.root.parent / "dispatcher_scan_cursor.txt"
        try:
            cursor = int(cursor_path.read_text().strip()) if cursor_path.exists() else 0
        except Exception:
            cursor = 0

        source = self.queue.bounded_candidates_window(limit, cursor)
        total = sum(1 for _ in self.queue.root.glob("*.json"))
        try:
            cursor_path.write_text(str((cursor + limit) % max(1, total)))
        except Exception:
            pass
        return source

    def dispatch_batch(self, max_dispatches: int = 8) -> list[DispatchResult]:
        # V65.76 scan-window starvation fix.
        # Keep the rotating window as the fast path, but before declaring idle
        # search the remaining eligible queue so ready work outside the current
        # window cannot be hidden by thousands of completed records.
        max_dispatches = max(1, min(int(max_dispatches), 64))
        scan_limit = max(
            max_dispatches * 16,
            int(os.getenv("COMPANYOS_QUEUE_SCAN_LIMIT", "1000")),
        )

        now = time.time()
        completed = self._completed_stage_index()
        source = self._window(scan_limit)

        try:
            from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
            boost_type = AdaptiveBackpressure(self.queue).decide().get("boost_type")
        except Exception:
            boost_type = None

        def eligible(task) -> bool:
            return (
                task.state == "QUEUED"
                and task.attempts < task.max_attempts
                and task.next_attempt_unix <= now
                and task.task_type in self.dispatcher.handlers
            )

        def sort_key(task):
            return (
                0 if boost_type and task.task_type == boost_type else 1,
                float(task.created_at_unix),
                -int(task.priority),
                task.task_id,
            )

        results: list[DispatchResult] = []
        dispatched_ids: set[str] = set()

        def drain(candidates) -> None:
            remaining = [
                t for t in candidates
                if t.task_id not in dispatched_ids
            ]
            remaining.sort(key=sort_key)

            while remaining and len(results) < max_dispatches:
                chosen_index = None
                for i, task in enumerate(remaining):
                    if self._dependency_satisfied_with_index(task, completed):
                        chosen_index = i
                        break

                if chosen_index is None:
                    break

                task = remaining.pop(chosen_index)
                result = self.dispatcher.dispatch_task(task)
                results.append(result)
                dispatched_ids.add(task.task_id)

                if result.dispatched and result.reason == "completed":
                    payload = self._payload(task)
                    goal_id = payload.get("goal_id")
                    stage = payload.get("stage")
                    if goal_id and stage:
                        completed.add((str(goal_id), str(stage)))

        # Fast rotating window first.
        drain([t for t in source if eligible(t)])

        # V65.76 starvation fallback: only pay for a whole-queue scan if the
        # fast path could not fill the requested batch.
        if len(results) < max_dispatches:
            fallback = [
                t for t in self.queue._iter_task_files()
                if eligible(t) and t.task_id not in dispatched_ids
            ]
            drain(fallback)

        if not results:
            results.append(
                DispatchResult(
                    False,
                    None,
                    None,
                    None,
                    "no_dependency_ready_task",
                    None,
                )
            )
        return results

    def dispatch_next(self) -> DispatchResult:
        return self.dispatch_batch(max_dispatches=1)[0]
