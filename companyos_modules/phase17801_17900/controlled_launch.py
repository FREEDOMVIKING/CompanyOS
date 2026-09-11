#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase17801_17900"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class LaunchGateState:
    stage: str
    ready_for_controlled_beta: bool
    ready_for_external_launch: bool
    external_actions_require_existing_gate: bool
    financial_actions_require_existing_gate: bool
    rollback_available: bool
    blockers: list[str]
    generated_at: float


class ControlledLaunchManager:
    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write(path: Path, payload: Any) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def _append(path: Path, payload: Any) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    @staticmethod
    def _id(payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True).encode()
        return "launch_" + hashlib.sha256(raw).hexdigest()[:12]

    def local_ai_reachable(self, host: str = "127.0.0.1", port: int = 8080) -> bool:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            return False

    def service_health(self) -> dict[str, Any]:
        try:
            process_text = subprocess.check_output(
                ["ps", "-ef"], text=True, stderr=subprocess.DEVNULL
            )
        except Exception:
            process_text = ""

        checks = {
            "local_ai_process": "llama-server" in process_text,
            "local_ai_endpoint_8080": self.local_ai_reachable(),
            "portfolio_dashboard": (
                ROOT / "companyos_runtime/phase17601_17700/latest_executive_dashboard.json"
            ).exists(),
            "portfolio_command_center": (
                ROOT / "companyos_runtime/phase17701_17800/latest_command_center.json"
            ).exists(),
            "start_control": any(
                p.exists()
                for p in [
                    ROOT / "run_adaptive_local.sh",
                    ROOT / "local_ai/start_local_ai.sh",
                    ROOT / "start_companyos_local.sh",
                ]
            ),
            "stop_control": any(
                p.exists()
                for p in [
                    ROOT / "local_ai/stop_local_ai.sh",
                    ROOT / "stop_companyos.sh",
                ]
            ),
        }
        payload = {
            "generated_at": time.time(),
            "checks": checks,
            "healthy": all(checks.values()),
        }
        self._write(self.state_dir / "service_health.json", payload)
        return payload

    def dependency_graph(self) -> dict[str, Any]:
        payload = {
            "generated_at": time.time(),
            "startup_order": [
                "local_ai",
                "continuous_runtime",
                "executive_bundle",
                "portfolio_director",
                "portfolio_orchestrator",
                "launch_gate_manager",
            ],
            "dependencies": {
                "continuous_runtime": ["local_ai"],
                "portfolio_director": ["executive_bundle"],
                "portfolio_orchestrator": ["portfolio_director"],
                "launch_gate_manager": ["continuous_runtime", "portfolio_orchestrator"],
            },
        }
        self._write(self.state_dir / "dependency_graph.json", payload)
        return payload

    def evaluate(
        self,
        *,
        phase_verified: bool,
        tests_passed: bool,
        state_persistent: bool,
        start_stop_present: bool,
        local_ai_ok: bool,
        soak_passed: bool,
        explicit_external_approval: bool = False,
    ) -> LaunchGateState:
        required = {
            "phase_verified": phase_verified,
            "tests_passed": tests_passed,
            "state_persistent": state_persistent,
            "start_stop_present": start_stop_present,
            "local_ai_ok": local_ai_ok,
        }
        blockers = [name for name, ok in required.items() if not ok]
        controlled = not blockers
        external = controlled and soak_passed and explicit_external_approval

        if controlled and not soak_passed:
            blockers.append("extended_soak_test_incomplete")
        if controlled and soak_passed and not explicit_external_approval:
            blockers.append("explicit_external_launch_approval_required")

        stage = (
            "EXTERNAL_LAUNCH_READY"
            if external
            else "CONTROLLED_BETA_READY"
            if controlled
            else "NOT_READY"
        )
        state = LaunchGateState(
            stage=stage,
            ready_for_controlled_beta=controlled,
            ready_for_external_launch=external,
            external_actions_require_existing_gate=True,
            financial_actions_require_existing_gate=True,
            rollback_available=True,
            blockers=blockers,
            generated_at=time.time(),
        )
        data = asdict(state)
        self._write(self.state_dir / "launch_gate_state.json", data)
        self._append(
            self.state_dir / "launch_gate_audit.jsonl",
            {"event_id": self._id(data), "event": "launch_gate_evaluated", **data},
        )
        return state

    def soak(self, seconds: int = 10, interval: float = 1.0) -> dict[str, Any]:
        seconds = max(1, int(seconds))
        started = time.time()
        cycles = []
        while time.time() - started < seconds:
            health = self.service_health()
            probe = self.state_dir / "soak_probe.json"
            marker = {"cycle": len(cycles), "at": time.time()}
            self._write(probe, marker)
            state_ok = json.loads(probe.read_text())["cycle"] == len(cycles)
            cycles.append({
                "at": time.time(),
                "health": health["healthy"],
                "state_write": state_ok,
            })
            time.sleep(max(0.2, interval))

        result = {
            "duration_seconds": round(time.time() - started, 3),
            "cycles": len(cycles),
            "passed": all(row["health"] and row["state_write"] for row in cycles),
            "observations": cycles,
        }
        self._write(self.state_dir / "latest_soak_test.json", result)
        return result

    def deployment_manifest(self) -> dict[str, Any]:
        payload = {
            "generated_at": time.time(),
            "version": "1.0.0-rc1",
            "phase_start": 17801,
            "phase_end": 17900,
            "local_ai_endpoint": "http://127.0.0.1:8080",
            "external_actions_default": False,
            "financial_actions_default": False,
            "rollback_required": True,
            "launch_assessment": "python scripts/companyos_launch_readiness.py assess",
        }
        self._write(self.state_dir / "deployment_manifest.json", payload)
        return payload

    def rollback_checkpoint(self) -> dict[str, Any]:
        payload = {
            "created_at": time.time(),
            "phase": 17900,
            "rollback_available": True,
            "automatic_rollback_executed": False,
        }
        self._write(self.state_dir / "rollback_checkpoint.json", payload)
        return payload

    def demo(self) -> dict[str, Any]:
        health = self.service_health()
        graph = self.dependency_graph()
        manifest = self.deployment_manifest()
        checkpoint = self.rollback_checkpoint()
        state = self.evaluate(
            phase_verified=True,
            tests_passed=True,
            state_persistent=True,
            start_stop_present=health["checks"]["start_control"] and health["checks"]["stop_control"],
            local_ai_ok=health["checks"]["local_ai_endpoint_8080"],
            soak_passed=False,
            explicit_external_approval=False,
        )
        return {
            "ok": True,
            "health": health,
            "startup_order": graph["startup_order"],
            "launch_gate": asdict(state),
            "deployment_version": manifest["version"],
            "rollback_available": checkpoint["rollback_available"],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["demo", "health", "soak", "manifest", "status"])
    parser.add_argument("--seconds", type=int, default=10)
    args = parser.parse_args()
    manager = ControlledLaunchManager()

    if args.action == "demo":
        result = manager.demo()
    elif args.action == "health":
        result = manager.service_health()
    elif args.action == "soak":
        result = manager.soak(args.seconds)
    elif args.action == "manifest":
        result = manager.deployment_manifest()
    else:
        result = {"ok": True, "files": sorted(p.name for p in manager.state_dir.glob("*"))}

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
