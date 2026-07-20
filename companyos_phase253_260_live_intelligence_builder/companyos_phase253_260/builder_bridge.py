from __future__ import annotations
from pathlib import Path
from companyos_phase205_212 import BuildTestRepairLoop, IsolatedWorkspace, SelfIntegrationEngine
from companyos_phase213_220 import CapabilityRegistry
from companyos_phase221_228 import ContextPackager, GitTransaction, RegressionGuard
from .context_budgeter import ContextBudgeter
from .execution_budget import ExecutionBudget
from .openrouter_adapter import OpenRouterCoderAdapter
from .repair_controller import RepairController

class BuilderBridge:
    """259: connect live intelligence to isolation, tests, repair, integration, and regression."""

    def __init__(self, project_root, adapter=None):
        self.root = Path(project_root).resolve()
        self.adapter = adapter or OpenRouterCoderAdapter()
        self.workspaces = IsolatedWorkspace()
        self.verifier = BuildTestRepairLoop()
        self.integrator = SelfIntegrationEngine()
        self.registry = CapabilityRegistry(self.root)
        self.git = GitTransaction()
        self.regression = RegressionGuard()
        self.context = ContextPackager()
        self.context_budget = ContextBudgeter()
        self.repair = RepairController()
        self.execution_budget = ExecutionBudget()

    def _write_files(self, workspace, files):
        root = Path(workspace)
        written = []
        for rel, content in files.items():
            p = Path(rel)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"unsafe model path: {rel}")
            target = root / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(str(p))
        return written

    def build(self, capability, module_name, mission, targeted_test=None):
        if not self.adapter.configured:
            return {"success": False, "stage": "configuration", "reason": "OPENROUTER_API_KEY_not_loaded"}

        checkpoint = self.git.begin(self.root)
        ws = self.workspaces.create(self.root)
        limits = self.execution_budget.limits()

        try:
            base_payload = {
                "task": "Implement this missing CompanyOS capability.",
                "capability": capability,
                "module_name": module_name,
                "mission": mission,
                "context": self.context_budget.trim(self.context.collect(self.root), max_chars=90000),
                "acceptance": [
                    "Python compilation passes",
                    "targeted tests pass",
                    "full existing test suite has no regression",
                ],
            }

            prompt = base_payload
            history = []

            for attempt in range(1, limits["max_repair_attempts"] + 1):
                generated = self.adapter.generate(prompt)
                if not generated.get("success"):
                    return {"success": False, "stage": "model_generation", "attempt": attempt, "generation": generated, "history": history}

                written = self._write_files(ws["workspace"], generated["files"])
                verify = self.verifier.bounded_cycle(ws["workspace"], max_attempts=1, targeted_test=targeted_test)
                history.append({
                    "attempt": attempt,
                    "model": generated.get("model"),
                    "usage": generated.get("usage", {}),
                    "written_files": written,
                    "verification": verify,
                })

                if verify.get("success"):
                    integration = self.integrator.integrate(ws["workspace"], self.root, module_name, {"success": True})
                    if not integration.get("integrated"):
                        return {"success": False, "stage": "integration", "integration": integration, "history": history}

                    regression = self.regression.run(self.root, targeted_test=targeted_test)
                    if not regression.get("success"):
                        rollback = self.git.rollback(self.root, checkpoint.get("checkpoint"))
                        return {"success": False, "stage": "live_regression", "regression": regression, "rollback": rollback, "history": history}

                    record = {
                        "module": module_name,
                        "verified": True,
                        "source": "openrouter_live_intelligence",
                        "model": generated.get("model"),
                        "mission": mission,
                    }
                    self.registry.register(capability, record)
                    commit = self.git.commit_all(self.root, f"CompanyOS autonomous build: {capability}")

                    return {
                        "success": True,
                        "status": "live_intelligence_autonomous_build_completed",
                        "capability": capability,
                        "module": module_name,
                        "history": history,
                        "integration": integration,
                        "regression": regression,
                        "git_commit": commit,
                        "registered": record,
                        "real_model_used": True,
                    }

                prompt = self.repair.make_prompt(base_payload, verify, attempt)

            return {"success": False, "stage": "repair_limit", "history": history}
        finally:
            self.workspaces.destroy(ws["container"])
