#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase689_704 import (
    PreflightCheck,RollbackPolicy,PolicyViolation,SafeMode,
    DecisionProvenance,GovernanceLedger,EscalationQueue
)

root=Path.home()/"companyos"

action={
    "action_type":"deploy_production",
    "external":True,
    "mutates_state":True,
    "reversible":True,
    "financial_commitment_usd":0,
}

preflight=PreflightCheck().run(action)
rollback=RollbackPolicy().evaluate(action)
safe=SafeMode(root).status()
violation=PolicyViolation().detect(preflight,rollback,safe)
record=DecisionProvenance().build(action,preflight,violation)
GovernanceLedger(root).append(record)

if violation["violation"]:
    EscalationQueue(root).add({
        "action":action,
        "governance":record,
        "requested_decision":"approve_or_reject"
    })

print(json.dumps({
    "preflight":preflight,
    "rollback":rollback,
    "safe_mode":safe,
    "violation":violation,
    "provenance":record,
},indent=2))
