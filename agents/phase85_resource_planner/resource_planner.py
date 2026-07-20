import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def plan(resources=None, monthly_budget_limit=0):
    resources = resources or []
    estimated = sum(float(r.get("estimated_monthly_cost", 0)) for r in resources)
    requires_approval = estimated > 0
    return {
        "success": True,
        "status": "phase85_resource_plan_complete",
        "resources": resources,
        "estimated_monthly_cost": round(estimated, 2),
        "monthly_budget_limit": float(monthly_budget_limit),
        "financial_commitment": estimated > 0,
        "approval_required": requires_approval,
        "created_at": now(),
    }

def status():
    return {"success": True, "status": "phase85_resource_planner_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
