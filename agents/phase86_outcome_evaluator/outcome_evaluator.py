import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def evaluate(targets, actuals):
    metrics = {}
    passed = 0
    total = 0
    for key, target in (targets or {}).items():
        actual = (actuals or {}).get(key)
        ok = actual is not None and actual >= target
        metrics[key] = {"target": target, "actual": actual, "passed": ok}
        total += 1
        passed += int(ok)
    score = round((passed / total * 100.0), 2) if total else 0.0
    return {
        "success": True,
        "status": "phase86_outcome_evaluation_complete",
        "score": score,
        "metrics": metrics,
        "evaluated_at": now(),
    }

def status():
    return {"success": True, "status": "phase86_outcome_evaluator_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
