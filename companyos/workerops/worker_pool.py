from .job_claim import JobClaimEngine
from .dedupe import JobDedupeEngine
from .backpressure import BackpressureController
from .worker_router import WorkerRouter
from .execution_bridge import ExecutionBridge
from .retry_policy import RetryPolicy
from .completion_store import CompletionStore

class DurableWorkerPool:
    def __init__(self, root):
        self.root=root
        self.completions=CompletionStore(root)

    def process_one(self, queue, worker_id="worker_1", tick=0, max_attempts=3):
        jobs=queue.load()
        pending=[j for j in jobs if j.get("status") in ("queued","retry")]
        pending.sort(key=lambda x:(-int(x.get("priority",0)),x.get("created_at","")))
        if not pending:
            return {"processed":False,"reason":"queue_empty"}

        backpressure=BackpressureController().evaluate(len(pending))
        job=pending[0]
        dedupe=JobDedupeEngine()
        key=dedupe.key(job)

        if dedupe.is_duplicate(job,self.completions.load()):
            queue.update(job["job_id"],status="complete",deduped=True)
            return {"processed":True,"deduped":True,"job_id":job["job_id"],"backpressure":backpressure}

        claimed=JobClaimEngine().claim(job,worker_id,tick=tick)
        claim_updates = dict(claimed)
        claim_updates.pop('job_id', None)
        queue.update(job['job_id'], **claim_updates)

        department=WorkerRouter().route(claimed)
        result=ExecutionBridge(self.root).execute(claimed,department)
        decision=RetryPolicy().decide(claimed,result,max_attempts=max_attempts)

        if decision["action"]=="complete":
            queue.update(job["job_id"],status="complete",result=result,lease_expiry_tick=0)
            self.completions.add(key)
        elif decision["action"]=="retry":
            queue.update(job["job_id"],status="retry",result=result,claimed_by=None)
        else:
            queue.update(job["job_id"],status="dead_letter",result=result)

        return {
            "processed":True,
            "job_id":job["job_id"],
            "department":department,
            "decision":decision,
            "result":result,
            "backpressure":backpressure
        }
