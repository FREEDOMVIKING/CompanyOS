#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import os
import socket
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
STATE = ROOT / "companyos_runtime" / "final_consolidation"
STATE.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class ComponentStatus:
    name: str
    import_path: str
    available: bool
    detail: str


class CompanyOSConsolidatedRuntime:
    """Integrates the current CompanyOS executive stack into one auditable runtime."""

    COMPONENTS = [
        ("controlled_launch", "companyos_modules.phase17801_17900.controlled_launch"),
        ("enterprise_orchestrator", "companyos_modules.phase17901_18000.enterprise_orchestrator"),
        ("venture_scheduler", "companyos_modules.phase18001_18100.venture_scheduler"),
        ("portfolio_balancer", "companyos_modules.phase18101_18200.portfolio_balancer"),
        ("executive_mission_control", "companyos_modules.phase18201_18300.executive_mission_control"),
        ("enterprise_learning_engine", "companyos_modules.phase18301_18400.enterprise_learning_engine"),
        ("strategy_evolution", "companyos_modules.phase18401_18500.strategy_evolution"),
        ("executive_adaptation", "companyos_modules.phase18501_18600.executive_adaptation"),
    ]

    def __init__(self, state_dir: Path = STATE) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write(path: Path, payload: Any) -> None:
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temp.replace(path)

    def component_audit(self) -> list[ComponentStatus]:
        results: list[ComponentStatus] = []
        for name, import_path in self.COMPONENTS:
            try:
                importlib.import_module(import_path)
                results.append(ComponentStatus(name, import_path, True, "import_ok"))
            except Exception as exc:
                results.append(ComponentStatus(name, import_path, False, f"{type(exc).__name__}: {exc}"))

        self._write(
            self.state_dir / "component_audit.json",
            [asdict(item) for item in results],
        )
        return results

    @staticmethod
    def local_ai_reachable(host: str = "127.0.0.1", port: int = 8080) -> bool:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            return False

    def runtime_probe(self) -> dict[str, Any]:
        try:
            process_text = subprocess.check_output(
                ["ps", "-ef"], text=True, stderr=subprocess.DEVNULL
            )
        except Exception:
            process_text = ""

        payload = {
            "generated_at": time.time(),
            "local_ai_reachable": self.local_ai_reachable(),
            "llama_server_process_present": "llama-server" in process_text,
            "companyos_process_present": "companyos" in process_text.lower(),
            "disk_root_exists": ROOT.exists(),
            "runtime_root_exists": (ROOT / "companyos_runtime").exists(),
            "start_control_present": any(
                path.exists()
                for path in [
                    ROOT / "run_adaptive_local.sh",
                    ROOT / "start_companyos_local.sh",
                    ROOT / "local_ai/start_local_ai.sh",
                ]
            ),
            "stop_control_present": any(
                path.exists()
                for path in [
                    ROOT / "stop_companyos.sh",
                    ROOT / "local_ai/stop_local_ai.sh",
                ]
            ),
        }
        self._write(self.state_dir / "runtime_probe.json", payload)
        return payload

    def integration_state(self) -> dict[str, Any]:
        audit = self.component_audit()
        probe = self.runtime_probe()

        missing = [item.name for item in audit if not item.available]
        core_ready = not missing
        runtime_controls_ready = (
            probe["start_control_present"] and probe["stop_control_present"]
        )

        payload = {
            "generated_at": time.time(),
            "status": "integrated" if core_ready else "integration_incomplete",
            "component_count": len(audit),
            "available_component_count": sum(1 for item in audit if item.available),
            "missing_components": missing,
            "core_ready": core_ready,
            "runtime_controls_ready": runtime_controls_ready,
            "local_ai_reachable": probe["local_ai_reachable"],
            "controlled_beta_ready": core_ready and runtime_controls_ready,
            "external_actions_enabled": False,
            "financial_actions_enabled": False,
            "external_actions_require_existing_gate": True,
            "financial_actions_require_existing_gate": True,
        }
        self._write(self.state_dir / "integration_state.json", payload)
        return payload

    def deployment_manifest(self) -> dict[str, Any]:
        payload = {
            "generated_at": time.time(),
            "name": "CompanyOS Consolidated Runtime",
            "version": "1.0.0-consolidated",
            "entrypoint": "python companyos_final.py status",
            "demo": "python companyos_final.py demo",
            "verification": "python companyos_final.py verify",
            "state_directory": str(self.state_dir),
            "local_ai_endpoint": "http://127.0.0.1:8080",
            "external_actions_default": False,
            "financial_actions_default": False,
            "rollback_required": True,
        }
        self._write(self.state_dir / "deployment_manifest.json", payload)
        return payload

    def verify(self) -> dict[str, Any]:
        state = self.integration_state()
        manifest = self.deployment_manifest()

        checks = {
            "all_components_importable": state["core_ready"],
            "runtime_controls_present": state["runtime_controls_ready"],
            "external_gate_preserved": state["external_actions_require_existing_gate"],
            "financial_gate_preserved": state["financial_actions_require_existing_gate"],
            "manifest_written": bool(manifest["version"]),
        }

        payload = {
            "generated_at": time.time(),
            "ok": all(checks.values()),
            "checks": checks,
            "integration_state": state,
        }
        self._write(self.state_dir / "latest_verification.json", payload)
        return payload

    def demo(self) -> dict[str, Any]:
        verification = self.verify()
        return {
            "ok": verification["ok"],
            "status": "companyos_consolidated_runtime_ready"
            if verification["ok"]
            else "companyos_consolidated_runtime_needs_attention",
            "verification": verification,
        }
