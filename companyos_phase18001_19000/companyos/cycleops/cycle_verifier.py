from .outcome_classifier import OutcomeClassifier

class CycleVerifier:
    def verify_execution(self, job, execution):
        outcome = OutcomeClassifier().classify(job, execution)
        checks = {
            "job_present": bool(job),
            "execution_present": bool(execution),
            "resolved": bool(outcome["resolved"]),
        }
        return {
            "passed": all(checks.values()),
            "checks": checks,
            "job_id": (job or {}).get("job_id"),
            "outcome": outcome
        }

    def summarize_cycle(self, rows):
        states = {
            "completed": 0,
            "deferred_for_approval": 0,
            "deduplicated": 0,
            "failed": 0,
        }
        resolved = 0

        for row in rows:
            outcome = (row.get("verification") or {}).get("outcome") or {}
            state = outcome.get("state", "failed")
            states[state] = states.get(state, 0) + 1
            if outcome.get("resolved"):
                resolved += 1

        total = len(rows)
        unresolved = total - resolved

        return {
            "total": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "completed": states.get("completed", 0),
            "deferred_for_approval": states.get("deferred_for_approval", 0),
            "deduplicated": states.get("deduplicated", 0),
            "failed": states.get("failed", 0),
            "cycle_verified": total > 0 and unresolved == 0
        }
