from .worker_pool import PersistentWorkerPool
from .job_dispatch import JobDispatcher
from .workflow_runtime import WorkflowRuntime
from .venture_spawner import VentureSpawner
from .service_supervisor import LongRunningServiceSupervisor
from .retry_engine import AdaptiveRetryEngine
from .recovery_coordinator import DeepRecoveryCoordinator
from .backpressure import BackpressureController
from .execution_checkpoint import ExecutionCheckpoint
from .scheduler_runtime import LongRunningScheduler
from .department_workflows import CrossDepartmentWorkflowEngine
from .runtime_metrics import ExecutionMetrics
from .execution_guardrails import ExecutionGuardrails
from .execution_audit import ExecutionAudit

class CEOExecutionFabric:
    def __init__(self, root):
        self.root=root
        self.pool=PersistentWorkerPool(root)
        self.checkpoint=ExecutionCheckpoint(root)
        self.audit=ExecutionAudit(root)

    def run(self, objective, workers=None, schedules=None, services=None, failures=None, actions=None, spawn_venture=False):
        worker_state=self.pool.ensure(workers or [])
        workflow_steps=CrossDepartmentWorkflowEngine().build(objective)
        workflow=WorkflowRuntime().start(objective,workflow_steps)
        jobs=LongRunningScheduler().expand(schedules or [])
        if not jobs:
            jobs=[{"name":s["name"],"capability":s["capability"],"priority":7} for s in workflow_steps]

        assignments=JobDispatcher().dispatch(jobs,list(worker_state.values()))
        service_actions=LongRunningServiceSupervisor().evaluate(services or [])
        recoveries=DeepRecoveryCoordinator().plan(failures or [])
        backpressure=BackpressureController().evaluate(
            backlog=sum(1 for x in assignments if x["status"]=="queued"),
            workers=max(1,len(worker_state))
        )

        gated=[]; autonomous=[]
        for a in actions or []:
            g=ExecutionGuardrails().evaluate(a)
            (gated if g["requires_approval"] else autonomous).append({**a,"guardrail":g})

        venture=VentureSpawner().spawn(objective,[],500) if spawn_venture else None
        metrics=ExecutionMetrics().summarize(assignments,recoveries,service_actions)

        result={
            "success":True,
            "status":"autonomous_runtime_execution_fabric_cycle_complete",
            "objective":objective,
            "workflow":workflow,
            "assignments":assignments,
            "service_supervision":service_actions,
            "recoveries":recoveries,
            "backpressure":backpressure,
            "autonomous_actions":autonomous,
            "approval_queue":gated,
            "spawned_venture":venture,
            "metrics":metrics,
        }

        self.checkpoint.save(result)
        self.audit.append("execution_cycle",result)
        return result
