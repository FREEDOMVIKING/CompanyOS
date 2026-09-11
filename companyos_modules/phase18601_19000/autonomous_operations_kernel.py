#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase18601_19000"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class WorkItem:
    work_id: str
    venture_id: str
    title: str
    priority: float
    expected_value: float
    risk_score: float
    dependencies: list[str]
    required_capabilities: list[str]
    external_action: bool = False
    financial_action: bool = False
    irreversible: bool = False
    status: str = "queued"


@dataclass(slots=True)
class ExecutionResult:
    work_id: str
    venture_id: str
    status: str
    action: str
    reason: str
    score: float
    receipt_id: str


class AutonomousOperationsKernel:
    """
    Long-running internal execution kernel.

    This kernel may autonomously plan, prioritize, route, execute internal work,
    checkpoint state, recover from internal failures, and generate dashboards.
    External, financial, and irreversible actions remain behind existing gates.
    """

    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.queue_path = self.state_dir / "work_queue.json"
        self.state_path = self.state_dir / "kernel_state.json"
        self.ledger_path = self.state_dir / "execution_ledger.jsonl"
        self.dashboard_path = self.state_dir / "executive_dashboard.json"

    @staticmethod
    def _write(path: Path, payload: Any) -> None:
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temp.replace(path)

    @staticmethod
    def _append(path: Path, payload: Any) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    @staticmethod
    def _id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"

    @staticmethod
    def _score(item: WorkItem) -> float:
        if item.status not in {"queued", "retry"}:
            return -1.0
        priority = max(0.0, min(100.0, item.priority)) / 100.0
        value = max(0.0, item.expected_value)
        risk = max(0.0, min(1.0, item.risk_score))
        gate_penalty = 0.30 if (
            item.external_action or item.financial_action or item.irreversible
        ) else 0.0
        return round(
            priority * 0.40
            + value * 0.35
            + (1.0 - risk) * 0.25
            - gate_penalty,
            6,
        )

    def load_queue(self) -> list[WorkItem]:
        if not self.queue_path.exists():
            return []
        raw = json.loads(self.queue_path.read_text(encoding="utf-8"))
        return [WorkItem(**row) for row in raw]

    def save_queue(self, items: list[WorkItem]) -> None:
        self._write(self.queue_path, [asdict(item) for item in items])

    def enqueue(self, items: list[WorkItem]) -> dict[str, Any]:
        current = {item.work_id: item for item in self.load_queue()}
        added = 0

        for item in items:
            if item.work_id not in current:
                current[item.work_id] = item
                added += 1

        queue = list(current.values())
        self.save_queue(queue)

        payload = {
            "generated_at": time.time(),
            "added": added,
            "queue_size": len(queue),
        }
        self._append(
            self.ledger_path,
            {
                "event": "work_enqueued",
                "event_id": self._id("enqueue", payload),
                **payload,
            },
        )
        return payload

    @staticmethod
    def _gate_reason(item: WorkItem) -> str | None:
        if item.irreversible:
            return "irreversible_action_requires_existing_gate"
        if item.financial_action:
            return "financial_action_requires_existing_gate"
        if item.external_action:
            return "external_action_requires_existing_gate"
        return None

    def select_ready(
        self,
        queue: list[WorkItem],
        completed_ids: set[str],
        capabilities: set[str],
    ) -> list[WorkItem]:
        ready = []

        for item in queue:
            if item.status not in {"queued", "retry"}:
                continue
            if not all(dep in completed_ids for dep in item.dependencies):
                continue
            if not all(cap in capabilities for cap in item.required_capabilities):
                continue
            ready.append(item)

        ready.sort(key=self._score, reverse=True)
        return ready

    def execute_internal(self, item: WorkItem) -> ExecutionResult:
        gate_reason = self._gate_reason(item)

        if gate_reason:
            item.status = "awaiting_existing_gate"
            action = "hold"
            reason = gate_reason
        else:
            item.status = "completed"
            action = "execute_internal"
            reason = "internal_work_completed"

        receipt_payload = {
            "work_id": item.work_id,
            "venture_id": item.venture_id,
            "status": item.status,
            "action": action,
            "reason": reason,
            "score": self._score(item),
            "completed_at": time.time(),
            "external_action_executed": False,
            "financial_action_executed": False,
            "irreversible_action_executed": False,
        }
        receipt_id = self._id("execution", receipt_payload)
        receipt_payload["receipt_id"] = receipt_id
        self._append(self.ledger_path, receipt_payload)

        return ExecutionResult(
            work_id=item.work_id,
            venture_id=item.venture_id,
            status=item.status,
            action=action,
            reason=reason,
            score=self._score(item),
            receipt_id=receipt_id,
        )

    def run_cycle(
        self,
        *,
        capabilities: set[str],
        max_items: int = 3,
    ) -> dict[str, Any]:
        queue = self.load_queue()
        completed_ids = {
            item.work_id for item in queue if item.status == "completed"
        }
        ready = self.select_ready(queue, completed_ids, capabilities)

        results: list[ExecutionResult] = []
        for item in ready[: max(1, int(max_items))]:
            results.append(self.execute_internal(item))

        self.save_queue(queue)

        blocked_dependency = [
            item.work_id
            for item in queue
            if item.status in {"queued", "retry"}
            and not all(dep in completed_ids for dep in item.dependencies)
        ]
        missing_capability = [
            item.work_id
            for item in queue
            if item.status in {"queued", "retry"}
            and not all(cap in capabilities for cap in item.required_capabilities)
        ]
        awaiting_gate = [
            item.work_id
            for item in queue
            if item.status == "awaiting_existing_gate"
        ]

        payload = {
            "generated_at": time.time(),
            "executed_count": sum(
                1 for result in results if result.status == "completed"
            ),
            "held_for_gate_count": sum(
                1 for result in results
                if result.status == "awaiting_existing_gate"
            ),
            "results": [asdict(result) for result in results],
            "blocked_dependency_ids": blocked_dependency,
            "missing_capability_ids": missing_capability,
            "awaiting_gate_ids": awaiting_gate,
            "queue_size": len(queue),
        }
        self._write(self.state_path, payload)
        self.update_dashboard(queue, payload)
        return payload

    def recover(self) -> dict[str, Any]:
        queue = self.load_queue()
        repaired = []

        for item in queue:
            if item.status == "failed_internal":
                item.status = "retry"
                repaired.append(item.work_id)

        self.save_queue(queue)
        payload = {
            "generated_at": time.time(),
            "repaired_work_ids": repaired,
            "recovery_scope": "internal_state_only",
            "external_action_executed": False,
            "financial_action_executed": False,
        }
        self._write(self.state_dir / "latest_recovery.json", payload)
        return payload

    def update_dashboard(
        self,
        queue: list[WorkItem],
        cycle: dict[str, Any],
    ) -> dict[str, Any]:
        status_counts: dict[str, int] = {}
        for item in queue:
            status_counts[item.status] = status_counts.get(item.status, 0) + 1

        payload = {
            "generated_at": time.time(),
            "kernel_status": "online",
            "queue_size": len(queue),
            "status_counts": status_counts,
            "last_cycle": cycle,
            "external_actions_enabled": False,
            "financial_actions_enabled": False,
            "irreversible_actions_enabled": False,
            "external_actions_require_existing_gate": True,
            "financial_actions_require_existing_gate": True,
            "irreversible_actions_require_existing_gate": True,
        }
        self._write(self.dashboard_path, payload)
        return payload

    def status(self) -> dict[str, Any]:
        queue = self.load_queue()
        latest = (
            json.loads(self.state_path.read_text(encoding="utf-8"))
            if self.state_path.exists()
            else None
        )
        return {
            "ok": True,
            "kernel_status": "online",
            "queue_size": len(queue),
            "latest_cycle": latest,
            "dashboard_path": str(self.dashboard_path),
            "ledger_path": str(self.ledger_path),
            "external_actions_enabled": False,
            "financial_actions_enabled": False,
            "irreversible_actions_enabled": False,
        }

    def demo(self) -> dict[str, Any]:
        demo_dir = self.state_dir / "demo"
        demo = AutonomousOperationsKernel(demo_dir)

        items = [
            WorkItem(
                "research_alpha",
                "venture_alpha",
                "Research customer demand",
                95,
                0.90,
                0.12,
                [],
                ["research"],
            ),
            WorkItem(
                "build_alpha",
                "venture_alpha",
                "Build internal MVP",
                90,
                0.84,
                0.18,
                ["research_alpha"],
                ["python"],
            ),
            WorkItem(
                "validate_alpha",
                "venture_alpha",
                "Validate internally",
                86,
                0.78,
                0.16,
                ["build_alpha"],
                ["testing"],
            ),
            WorkItem(
                "publish_alpha",
                "venture_alpha",
                "Publish externally",
                92,
                0.88,
                0.25,
                ["validate_alpha"],
                ["deployment"],
                external_action=True,
                irreversible=True,
            ),
            WorkItem(
                "fund_beta",
                "venture_beta",
                "Transfer venture funds",
                88,
                0.82,
                0.30,
                [],
                ["finance"],
                financial_action=True,
                irreversible=True,
            ),
        ]

        demo.enqueue(items)
        capabilities = {"research", "python", "testing", "deployment", "finance"}

        cycles = []
        for _ in range(5):
            cycles.append(
                demo.run_cycle(
                    capabilities=capabilities,
                    max_items=3,
                )
            )

        return {
            "ok": True,
            "cycles": cycles,
            "status": demo.status(),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=["demo", "status", "cycle", "recover"],
    )
    parser.add_argument(
        "--capabilities",
        default="research,python,testing,analytics,operations",
    )
    parser.add_argument("--max-items", type=int, default=3)
    args = parser.parse_args()

    kernel = AutonomousOperationsKernel()

    if args.action == "demo":
        result = kernel.demo()
    elif args.action == "status":
        result = kernel.status()
    elif args.action == "recover":
        result = kernel.recover()
    else:
        capabilities = {
            value.strip()
            for value in args.capabilities.split(",")
            if value.strip()
        }
        result = kernel.run_cycle(
            capabilities=capabilities,
            max_items=args.max_items,
        )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
