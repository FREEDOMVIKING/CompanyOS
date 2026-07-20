import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def evaluate(requested_amount=0, approved_limit=0):
    requested = float(requested_amount)
    limit = float(approved_limit)

    if requested <= 0:
        decision = "no_financial_commitment"
        approval_required = False
    elif requested <= limit and limit > 0:
        decision = "within_preapproved_envelope"
        approval_required = False
    else:
        decision = "owner_approval_required"
        approval_required = True

    return {
        "success": True,
        "status": "phase106_budget_evaluated",
        "requested_amount": requested,
        "approved_limit": limit,
        "decision": decision,
        "approval_required": approval_required,
        "evaluated_at": now(),
    }

def status():
    return {"success": True, "status": "phase106_budget_envelope_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
