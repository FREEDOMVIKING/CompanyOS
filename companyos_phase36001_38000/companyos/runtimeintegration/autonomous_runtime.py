import time
from companyos.executionops import CapabilityDiscovery
from companyos.integrationops import StageExecutionBridge, IntegratedOperatingCycleExecutor
from companyos.runtimeops import RuntimeCheckpoint, RuntimeHealth
from .runtime_recovery import RuntimeRecoveryManager

class IntegratedAutonomousRuntime:
    def __init__(self, root, interval_seconds=300):
        self.root = root
        self.interval_seconds = int(interval_seconds)
        self.checkpoint = RuntimeCheckpoint(root)
        self.health = RuntimeHealth(root)
        self.recovery = RuntimeRecoveryManager()

    def run_once(self, stage_payloads=None, treasury_policy_satisfied=True):
        capabilities = CapabilityDiscovery(self.root).discover()
        bridge = StageExecutionBridge(self.root, available_capabilities=set(capabilities.keys()))
        executor = IntegratedOperatingCycleExecutor(bridge)

        cycle = executor.run(
            stage_payloads=stage_payloads or {},
            treasury_policy_satisfied=treasury_policy_satisfied
        )
        recovery = self.recovery.classify_cycle(cycle)

        result = {
            "success": cycle.get("success", False),
            "capabilities": capabilities,
            "cycle": cycle,
            "recovery": recovery,
            "health": self.health.snapshot(),
        }
        self.checkpoint.save(result)
        return result

    def run_forever(self, stage_payloads=None, treasury_policy_satisfied=True, max_cycles=None):
        cycles = 0
        last = None

        while True:
            last = self.run_once(
                stage_payloads=stage_payloads,
                treasury_policy_satisfied=treasury_policy_satisfied
            )
            cycles += 1

            if max_cycles is not None and cycles >= int(max_cycles):
                return {
                    "success": True,
                    "cycles": cycles,
                    "last": last
                }

            next_action = last.get("recovery", {}).get("next_action")
            if next_action == "wait_for_approval_then_resume":
                time.sleep(max(self.interval_seconds, 60))
            else:
                time.sleep(max(self.interval_seconds, 5))
