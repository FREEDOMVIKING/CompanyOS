#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase19001_19500"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class RuntimeSignal:
    component: str
    healthy: bool
    latency_ms: float
    error_rate: float
    queue_depth: int
    last_success_age_seconds: float
    restart_count: int
    critical: bool = False


@dataclass(slots=True)
class SupervisorDecision:
    component: str
    action: str
    reason: str
    severity: str
    autonomous_internal_action: bool
    external_action_executed: bool
    financial_action_executed: bool


class ProductionSupervisor:
    """Supervises continuous CompanyOS runtime health and internal recovery."""

    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = self.state_dir / "supervisor_ledger.jsonl"

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
    def health_score(signal: RuntimeSignal) -> float:
        score = 1.0
        if not signal.healthy:
            score -= 0.45
        score -= min(0.20, max(0.0, signal.error_rate) * 0.40)
        score -= min(0.15, max(0.0, signal.latency_ms - 500.0) / 5000.0)
        score -= min(0.10, max(0, signal.queue_depth - 20) / 200.0)
        score -= min(
            0.10,
            max(0.0, signal.last_success_age_seconds - 300.0) / 3600.0,
        )
        return round(max(0.0, min(1.0, score)), 6)

    def evaluate(self, signals: list[RuntimeSignal]) -> list[SupervisorDecision]:
        decisions: list[SupervisorDecision] = []

        for signal in signals:
            score = self.health_score(signal)

            if signal.critical and not signal.healthy:
                action = "enter_safe_internal_mode"
                reason = "critical_component_unhealthy"
                severity = "critical"
            elif not signal.healthy and signal.restart_count < 3:
                action = "restart_internal_component"
                reason = "component_unhealthy_restart_available"
                severity = "high"
            elif signal.error_rate >= 0.25:
                action = "quarantine_and_retry"
                reason = "error_rate_above_threshold"
                severity = "high"
            elif signal.queue_depth >= 50:
                action = "rebalance_internal_workload"
                reason = "queue_pressure_detected"
                severity = "medium"
            elif signal.latency_ms >= 2000:
                action = "reduce_internal_concurrency"
                reason = "latency_threshold_exceeded"
                severity = "medium"
            elif signal.last_success_age_seconds >= 1800:
                action = "run_internal_probe"
                reason = "stale_success_signal"
                severity = "medium"
            else:
                action = "continue"
                reason = "component_healthy"
                severity = "low"

            decisions.append(
                SupervisorDecision(
                    component=signal.component,
                    action=action,
                    reason=reason,
                    severity=severity,
                    autonomous_internal_action=action != "continue",
                    external_action_executed=False,
                    financial_action_executed=False,
                )
            )

        payload = {
            "generated_at": time.time(),
            "decisions": [asdict(item) for item in decisions],
        }
        self._write(self.state_dir / "latest_supervisor_decisions.json", payload)
        self._append(
            self.ledger,
            {
                "event_id": self._id("supervisor", payload),
                "event": "runtime_supervision_cycle",
                **payload,
            },
        )
        return decisions

    def recovery_plan(
        self,
        decisions: list[SupervisorDecision],
    ) -> dict[str, Any]:
        steps = []
        for item in decisions:
            if item.action == "continue":
                continue
            steps.append(
                {
                    "component": item.component,
                    "action": item.action,
                    "checkpoint_before_action": True,
                    "rollback_on_failure": True,
                    "internal_only": True,
                    "external_action_executed": False,
                    "financial_action_executed": False,
                }
            )

        payload = {
            "generated_at": time.time(),
            "steps": steps,
            "external_actions_require_existing_gate": True,
            "financial_actions_require_existing_gate": True,
            "irreversible_actions_require_existing_gate": True,
        }
        self._write(self.state_dir / "latest_recovery_plan.json", payload)
        return payload

    def service_level_report(
        self,
        signals: list[RuntimeSignal],
    ) -> dict[str, Any]:
        scores = [self.health_score(signal) for signal in signals]
        healthy_count = sum(1 for signal in signals if signal.healthy)

        payload = {
            "generated_at": time.time(),
            "component_count": len(signals),
            "healthy_component_count": healthy_count,
            "unhealthy_component_count": len(signals) - healthy_count,
            "average_health_score": round(
                statistics.fmean(scores) if scores else 0.0,
                6,
            ),
            "critical_component_failures": [
                signal.component
                for signal in signals
                if signal.critical and not signal.healthy
            ],
            "production_ready": bool(signals)
            and healthy_count == len(signals)
            and all(score >= 0.75 for score in scores),
        }
        self._write(self.state_dir / "service_level_report.json", payload)
        return payload

    def soak_state(
        self,
        signals: list[RuntimeSignal],
        cycles_completed: int,
    ) -> dict[str, Any]:
        report = self.service_level_report(signals)
        payload = {
            "generated_at": time.time(),
            "cycles_completed": max(0, int(cycles_completed)),
            "service_level_report": report,
            "soak_passed": (
                cycles_completed >= 30
                and report["average_health_score"] >= 0.80
                and not report["critical_component_failures"]
            ),
        }
        self._write(self.state_dir / "soak_state.json", payload)
        return payload

    def dashboard(
        self,
        signals: list[RuntimeSignal],
        decisions: list[SupervisorDecision],
        recovery: dict[str, Any],
        soak: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "generated_at": time.time(),
            "status": "production_supervisor_online",
            "components": [
                {
                    "component": signal.component,
                    "health_score": self.health_score(signal),
                    "healthy": signal.healthy,
                }
                for signal in signals
            ],
            "active_internal_recovery_count": len(recovery["steps"]),
            "critical_decision_count": sum(
                1 for item in decisions if item.severity == "critical"
            ),
            "soak_passed": soak["soak_passed"],
            "external_actions_enabled": False,
            "financial_actions_enabled": False,
            "irreversible_actions_enabled": False,
        }
        self._write(self.state_dir / "production_dashboard.json", payload)
        return payload

    def demo(self) -> dict[str, Any]:
        signals = [
            RuntimeSignal(
                "autonomous_operations_kernel",
                True,
                120,
                0.01,
                8,
                15,
                0,
                critical=True,
            ),
            RuntimeSignal(
                "local_ai_endpoint",
                True,
                420,
                0.03,
                4,
                12,
                1,
                critical=True,
            ),
            RuntimeSignal(
                "venture_scheduler",
                True,
                180,
                0.02,
                12,
                30,
                0,
            ),
            RuntimeSignal(
                "portfolio_balancer",
                False,
                2400,
                0.30,
                58,
                1900,
                1,
            ),
        ]

        decisions = self.evaluate(signals)
        recovery = self.recovery_plan(decisions)
        soak = self.soak_state(signals, cycles_completed=30)
        dashboard = self.dashboard(signals, decisions, recovery, soak)

        return {
            "ok": True,
            "decisions": [asdict(item) for item in decisions],
            "recovery": recovery,
            "soak": soak,
            "dashboard": dashboard,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["demo", "status"])
    args = parser.parse_args()

    supervisor = ProductionSupervisor()
    if args.action == "demo":
        result = supervisor.demo()
    else:
        path = supervisor.state_dir / "production_dashboard.json"
        result = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.exists()
            else {"ok": True, "status": "no_supervisor_cycle_yet"}
        )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
