from .job_queue import PersistentJobQueue
from .heartbeat import RuntimeHeartbeat
from .watchdog import RuntimeWatchdog
from .scheduler import AutonomousScheduler
from .agent_return_bus import AgentReturnBus
from .resource_scheduler import CrossVentureResourceScheduler
from .checkpoint_store import CheckpointStore
from .restart_recovery import RestartSafeRecovery
from .cycle_engine import ContinuousCEOCycleEngine
from .runtime_control import UnifiedRuntimeControl
from .runtime_audit import RuntimeAudit
from .health_snapshot import RuntimeHealthSnapshot

class CEOCompanyRuntime:
    def __init__(self, root):
        self.root=root
        self.queue=PersistentJobQueue(root)
        self.heartbeat=RuntimeHeartbeat(root)
        self.bus=AgentReturnBus(root)
        self.checkpoints=CheckpointStore(root)
        self.audit=RuntimeAudit(root)

    def bootstrap(self, cadence, ventures=None, departments=None):
        schedule=AutonomousScheduler().plan(cadence or {})
        for j in schedule:
            self.queue.enqueue(j["task_type"],{"name":j["name"],"department":(departments or ["operations"])[0]},j["priority"])
        resources=CrossVentureResourceScheduler().allocate(ventures or [], max(1,len(departments or ["operations"])))
        beat=self.heartbeat.beat("company_runtime",{"status":"running"})
        snap=self.queue.snapshot()
        checkpoint=self.checkpoints.save({"queue":snap,"resources":resources})
        result={"schedule":schedule,"resources":resources,"heartbeat":beat,"checkpoint":checkpoint}
        self.audit.append("bootstrap",result)
        return result

    def run_cycle(self, departments=None):
        beat=self.heartbeat.beat("company_runtime",{"phase":"cycle"})
        cycle=ContinuousCEOCycleEngine().cycle(self.queue,departments or ["operations"])
        for item in cycle["processed"]:
            self.bus.publish(item)
        checkpoint=self.checkpoints.save({"queue":self.queue.snapshot(),"last_cycle":cycle})
        watchdog=RuntimeWatchdog().evaluate(beat)
        health=RuntimeHealthSnapshot().build(
            self.queue.snapshot(),
            watchdog,
            [{"service":"company_runtime","healthy":watchdog["healthy"]}],
            checkpoint
        )
        result={"success":True,"status":"company_runtime_cycle_complete","cycle":cycle,"health":health}
        self.audit.append("cycle",result)
        return result

    def recover(self):
        checkpoint=self.checkpoints.load()
        queue=self.queue.snapshot()
        recovery=RestartSafeRecovery().recover(checkpoint,queue)
        self.audit.append("recover",recovery)
        return recovery

    def status(self):
        beat=self.heartbeat.read()
        wd=RuntimeWatchdog().evaluate(beat)
        return UnifiedRuntimeControl().status(self.queue.snapshot(),beat,wd)
