from __future__ import annotations
from typing import Any, Mapping
from companyos.runtime_financial_queue import enqueue

def _get(x, *names, default=None):
    if isinstance(x, Mapping):
        for n in names:
            if x.get(n) is not None: return x[n]
    else:
        for n in names:
            if hasattr(x,n) and getattr(x,n) is not None: return getattr(x,n)
    return default

def queue_scheduler_financial_intent(intent: Any):
    action=str(_get(intent,"action_type","action",default="sol_transfer")).strip()
    destination=str(_get(intent,"destination","destination_address","to_address",default="")).strip()
    sol=float(_get(intent,"sol","amount_sol","amount",default=0.0))
    source_ref=str(_get(intent,"source_ref","intent_id","job_id","task_id","id",default="")).strip()
    idem=_get(intent,"idempotency_key",default=None)
    if not destination: raise ValueError("destination_required")
    if sol < 0: raise ValueError("negative_amount_rejected")
    return enqueue(action_type=action,destination=destination,sol=sol,
                   source_ref=source_ref,idempotency_key=str(idem) if idem else None)

dispatch_scheduler_financial_intent_to_queue=queue_scheduler_financial_intent
