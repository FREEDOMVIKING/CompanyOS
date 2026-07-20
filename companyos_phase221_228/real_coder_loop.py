from __future__ import annotations
from pathlib import Path
from companyos_phase205_212 import (
    CapabilityGapDetector,BuildSpecGenerator,IsolatedWorkspace,
    BuildTestRepairLoop,SelfIntegrationEngine,CapabilityGapDetector as _Unused
)
from companyos_phase213_220 import CapabilityRegistry,SelfBuildMission
from .context_packager import ContextPackager
from .coder_bridge import CoderBridge
from .patch_cycle import PatchCycle
from .git_transaction import GitTransaction
from .regression_guard import RegressionGuard
from .capability_promoter import CapabilityPromoter
from .autonomous_gap_builder import AutonomousGapBuilder

class RealCoderLoop:
    """228: real model-connected autonomous self-build loop."""

    def __init__(self,project_root,bridge=None):
        self.root=Path(project_root).resolve()
        self.gaps=CapabilityGapDetector()
        self.specs=BuildSpecGenerator()
        self.workspaces=IsolatedWorkspace()
        self.verifier=BuildTestRepairLoop()
        self.integrator=SelfIntegrationEngine()
        self.registry=CapabilityRegistry(self.root)
        self.missions=SelfBuildMission()
        self.context=ContextPackager()
        self.bridge=bridge or CoderBridge()
        self.patch=PatchCycle()
        self.git=GitTransaction()
        self.regression=RegressionGuard()
        self.promoter=CapabilityPromoter()
        self.selector=AutonomousGapBuilder()

    def inspect(self,goals,capabilities):
        gaps=self.gaps.detect(goals,capabilities,self.root)
        return {
            "success":True,
            "coder_configured":self.bridge.configured,
            "gaps":gaps,
            "selected_gap":self.selector.choose(gaps),
            "autonomy_mode":"high",
        }

    def build_selected_gap(self,goals,capabilities,max_attempts=3):
        if not self.bridge.configured:
            return {"success":False,"stage":"configuration","reason":"external_coder_not_configured"}

        gaps=self.gaps.detect(goals,capabilities,self.root)
        gap=self.selector.choose(gaps)
        if not gap:
            return {"success":True,"status":"no_capability_gap_detected"}

        spec=self.specs.generate(gap)
        mission=self.missions.create(gap,spec)
        checkpoint=self.git.begin(self.root)
        ws=self.workspaces.create(self.root)
        try:
            payload={
                "task":"Implement missing CompanyOS capability",
                "mission":mission,
                "build_spec":spec,
                "context":self.context.collect(self.root),
                "output_contract":{"files":{"relative/path.py":"content"}},
            }
            target_test=f"tests/test_{spec['module_name']}.py"
            cycle=self.patch.run(self.bridge,self.verifier,ws["workspace"],payload,targeted_test=target_test,max_attempts=max_attempts)
            if not cycle.get("success"):
                return {"success":False,"stage":"build_cycle","cycle":cycle,"mission":mission}

            verification={"success":True}
            integration=self.integrator.integrate(ws["workspace"],self.root,spec["module_name"],verification)
            if not integration.get("integrated"):
                return {"success":False,"stage":"integration","integration":integration}

            regress=self.regression.run(self.root,targeted_test=target_test)
            if not regress.get("success"):
                rollback=self.git.rollback(self.root,checkpoint.get("checkpoint"))
                return {"success":False,"stage":"regression","regression":regress,"rollback":rollback}

            commit=self.git.commit_all(self.root,f"CompanyOS autonomous capability: {spec['capability']}")
            record=self.promoter.promote(
                self.registry,spec["capability"],spec["module_name"],mission["mission_id"],
                model_metadata={"bridge_configured":True}
            )
            return {
                "success":True,
                "status":"phase228_real_coder_self_build_completed",
                "mission":mission,
                "cycle":cycle,
                "integration":integration,
                "regression":regress,
                "git_commit":commit,
                "registered_capability":record,
                "autonomy_mode":"high",
                "real_external_coder_used":True,
            }
        finally:
            self.workspaces.destroy(ws["container"])
