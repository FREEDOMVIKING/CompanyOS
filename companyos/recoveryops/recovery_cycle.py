import time
from .diagnostic_engine import DiagnosticEngine
from .retry_policy import RetryPolicy
from .missing_input_handler import MissingInputHandler

class AutonomousRecoveryCycle:
    def __init__(self, root, execution_bridge, verifier):
        self.root = root
        self.execution_bridge = execution_bridge
        self.verifier = verifier

    def recover_row(self, row):
        job = row.get("job") or {}
        execution = row.get("execution") or {}
        verification = row.get("verification") or {}

        diagnosis = DiagnosticEngine().diagnose(job, execution, verification)
        attempts = int((execution or {}).get("recovery_attempts", 0))
        decision = RetryPolicy().decision(diagnosis, attempts)

        if not decision["retry"]:
            return {
                "recovered": False,
                "diagnosis": diagnosis,
                "decision": decision,
                "row": row,
            }

        retry_job = job
        if diagnosis["kind"] == "missing_input":
            retry_job = MissingInputHandler().enrich(job)

        if decision["backoff_seconds"] > 0:
            time.sleep(min(decision["backoff_seconds"], 1))

        department = retry_job.get("department") or (retry_job.get("payload") or {}).get("department") or "operations"
        result = self.execution_bridge.execute(retry_job, department)

        if isinstance(result, dict):
            result = dict(result)
            result["recovery_attempts"] = decision["next_attempt"]

        new_verification = self.verifier.verify_execution(retry_job, result)

        return {
            "recovered": bool(new_verification.get("passed")),
            "diagnosis": diagnosis,
            "decision": decision,
            "row": {
                "job": retry_job,
                "execution": result,
                "verification": new_verification,
            }
        }

    def recover_unresolved(self, rows):
        output = []
        recovered = 0

        for row in rows:
            verification = row.get("verification") or {}
            if verification.get("passed"):
                output.append(row)
                continue

            rec = self.recover_row(row)
            output.append(rec["row"])
            if rec.get("recovered"):
                recovered += 1

        return {
            "rows": output,
            "recovered_count": recovered,
        }
