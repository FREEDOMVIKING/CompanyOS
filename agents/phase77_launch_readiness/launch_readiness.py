import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def assess(checks):
    required = {
        "problem_validated": False,
        "customer_defined": False,
        "mvp_tested": False,
        "revenue_path_defined": False,
        "risk_review_complete": False,
        "approval_boundary_clear": False,
    }
    required.update({k: bool(v) for k, v in (checks or {}).items() if k in required})

    passed = sum(1 for v in required.values() if v)
    ready = passed == len(required)

    return {
        "success": True,
        "status": "phase77_launch_ready" if ready else "phase77_launch_not_ready",
        "ready": ready,
        "passed_checks": passed,
        "total_checks": len(required),
        "checks": required,
        "external_launch_requires_owner_approval": True,
        "assessed_at": now(),
    }

def status():
    return {"success": True, "status": "phase77_launch_readiness_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
