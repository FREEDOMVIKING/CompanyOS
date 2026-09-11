from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import os, time

from companyos.canonicalruntime import UnifiedCEOCanonicalBridge
from companyos.canonicalorchestration import CanonicalOrchestrationBridge, GoalRequest
from companyos.canonicalexec import CanonicalExecutionGateway

from .state import ProductionStateStore
from .phase102_adapter import Phase102Adapter

class CanonicalProductionRuntime:
    def __init__(self, companyos_root: str | None = None):
        self.root = Path(companyos_root or os.environ.get(
            "COMPANYOS_ROOT", str(Path.home() / "companyos")
        ))
        self.runtime_root = self.root / "companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)

        self.state = ProductionStateStore(self.runtime_root)
        self.phase102 = Phase102Adapter(self.root)
        self.ceo = UnifiedCEOCanonicalBridge(str(self.root))
        self.orchestration = CanonicalOrchestrationBridge(str(self.root))
        self.gateway = CanonicalExecutionGateway(str(self.root))

    def status(self) -> Dict[str, Any]:
        p102 = self.phase102.status()
        out = {
            "ready": bool(
                p102.get("ready")
                and self.ceo.status().get("ready")
                and self.orchestration.status().get("ready")
                and self.gateway.status().get("ready")
            ),
            "phase102": p102,
            "ceo_bridge": self.ceo.status(),
            "orchestration": self.orchestration.status(),
            "execution_gateway": self.gateway.status(),
            "production_state": self.state.read(),
        }
        out["reason"] = "canonical_production_healthy" if out["ready"] else "canonical_production_not_ready"
        return out

    def start(self) -> Dict[str, Any]:
        before = self.phase102.status()
        start_result = None

        if not before.get("ready"):
            start_result = self.phase102.start()
            time.sleep(3)

        after = self.phase102.status()
        data = {
            "running": bool(after.get("ready")),
            "started_at": time.time(),
            "phase102_ready": bool(after.get("ready")),
            "broadcast_allowed": bool(self.gateway.status().get("broadcast_allowed")),
            "external_actions_allowed": bool(self.gateway.status().get("external_actions_allowed")),
        }
        self.state.write(data)
        self.state.append("production_start", {
            "before": before,
            "start_result": start_result,
            "after": after,
            "state": data,
        })
        return self.status()

    def stop(self) -> Dict[str, Any]:
        stop_result = self.phase102.stop()
        time.sleep(2)
        data = self.state.read()
        data.update({
            "running": False,
            "stopped_at": time.time(),
        })
        self.state.write(data)
        self.state.append("production_stop", {
            "stop_result": stop_result,
            "state": data,
        })
        return self.status()

    def once(self, objective: str = "Run one internal CompanyOS production validation cycle") -> Dict[str, Any]:
        goal = GoalRequest(
            objective=objective,
            context={"mode": "canonical_production_once"},
            source="canonical_production_runtime",
        )
        result = self.orchestration.run_goal(goal).to_dict()
        self.state.append("production_once", result)
        return result

    def test(self) -> Dict[str, Any]:
        test_goal = self.once("Run an internal end-to-end CompanyOS production smoke cycle")
        return {
            "phase102_available": self.phase102.available(),
            "goal_result": test_goal,
            "gateway": self.gateway.status(),
            "no_broadcast_expected": True,
            "pass": (
                test_goal.get("tasks_failed") == 0
                and self.gateway.status().get("ready") is True
            ),
        }
