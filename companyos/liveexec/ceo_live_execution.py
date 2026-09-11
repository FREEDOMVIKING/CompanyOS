from .execution_job import ExecutionJob
from .idempotency import IdempotencyStore
from .provider_invoker import ProviderInvoker
from .result_verifier import LiveResultVerifier
from .execution_router import ExecutionRouter
from .worker_runtime import LiveWorkerRuntime
from .receipt_store import LiveExecutionReceiptStore
from .observability import LiveExecutionObservability
from .failure_recovery import LiveFailureRecovery
from .approval_bridge import ApprovalExecutionBridge
from .execution_state import LiveExecutionState
from .execution_audit import LiveExecutionAudit

class CEOLiveExecutionController:
    def __init__(self,root):
        self.root=root
        self.idempotency=IdempotencyStore(root)
        self.receipts=LiveExecutionReceiptStore(root)
        self.state=LiveExecutionState(root)
        self.audit=LiveExecutionAudit(root)

    def run(self, requests, ranked_connectors, simulate=True):
        jobs=[]
        for r in requests or []:
            jobs.append(ExecutionJob().create(
                r.get("capability"),r.get("action"),r.get("payload",{}),
                r.get("priority",5),r.get("idempotency_key")
            ))

        split=ApprovalExecutionBridge().split(jobs)
        executions=[]
        skipped=[]
        for job in split["autonomous_jobs"]:
            key=job.get("idempotency_key")
            if key and self.idempotency.seen(key):
                skipped.append({"job":job,"reason":"idempotency_replay","result":self.idempotency.get(key)})
                continue
            route=ExecutionRouter().route(job,ranked_connectors)
            rec=LiveWorkerRuntime().execute_once(
                job,route.get("selected"),ProviderInvoker(),LiveResultVerifier(),simulate=simulate
            )
            executions.append(rec)
            self.receipts.append(rec)
            if rec.get("status")=="complete":
                self.idempotency.record(key,rec)

        failures=[x for x in executions if x.get("status")=="failed"]
        recovery=LiveFailureRecovery().plan(failures)
        obs=LiveExecutionObservability().summarize(executions)

        result={
            "success":True,
            "status":"live_capability_execution_control_cycle_complete",
            "simulate":bool(simulate),
            "autonomous_jobs":split["autonomous_jobs"],
            "approval_jobs":split["approval_jobs"],
            "executions":executions,
            "skipped":skipped,
            "recovery":recovery,
            "observability":obs
        }
        self.state.save(result)
        self.audit.append("liveexec_cycle",result)
        return result
