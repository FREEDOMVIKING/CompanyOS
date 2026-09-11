from companyos_phase705_720 import CEORuntimeBridge
from companyos_phase577_592 import CEOLifecycleBridge
from .test_mission_factory import TestMissionFactory
from .queue_injector import QueueInjector
from .cycle_probe import CycleProbe
from .lifecycle_probe import LifecycleProbe
from .learning_probe import LearningProbe
from .audit_probe import AuditProbe
from .state_probe import StateProbe
from .queue_probe import QueueProbe
from .integration_assertions import IntegrationAssertions
from .recovery_probe import RecoveryProbe

class EndToEndHarness:
    """733: run one controlled closed-loop mission integration test."""

    def __init__(self, root):
        self.root=root
        self.runtime=CEORuntimeBridge(root)
        self.injector=QueueInjector(root)
        self.state=StateProbe(root)
        self.lifecycle=LifecycleProbe(root)
        self.learning=LearningProbe(root)
        self.audit=AuditProbe(root)
        self.queue=QueueProbe(root)

    def run(self, venture_id="venture_integration_test", seed="default"):
        lifecycle_bridge=CEOLifecycleBridge(self.root)
        lifecycle_bridge.ensure_venture(
            "Integration Test Venture",
            "integration_test",
            stage="research",
            evidence={"validation_candidate_ready":False}
        )
        actual_id = lifecycle_bridge.ensure_venture(
            "Integration Test Venture",
            "integration_test",
            stage="research",
            evidence={"validation_candidate_ready":False}
        )["venture_id"]

        venture_id = actual_id
        mission=TestMissionFactory().create(venture_id=venture_id, mission_type="research", seed=seed)

        before=self.state.inspect()
        injected=self.injector.inject(mission)
        runtime_result=self.runtime.tick()
        after=self.state.inspect()
        venture=self.lifecycle.inspect(venture_id)
        learning=self.learning.inspect(venture_id)
        audits=self.audit.inspect()
        queue=self.queue.inspect()

        assertions=IntegrationAssertions().evaluate(before,after,venture,learning,audits)
        recovery=RecoveryProbe().evaluate(after,queue)

        return {
            "success":bool(assertions["passed"]) and recovery["recoverable"],
            "status":"end_to_end_integration_passed" if assertions["passed"] else "end_to_end_integration_failed",
            "mission":mission,
            "injected":injected,
            "runtime":runtime_result,
            "cycle_probe":CycleProbe().inspect(runtime_result),
            "before_state":before,
            "after_state":after,
            "venture":venture,
            "learning":learning,
            "audits":audits,
            "queue":queue,
            "assertions":assertions,
            "recovery":recovery,
        }
