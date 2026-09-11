class MissingInputHandler:
    def enrich(self, job):
        job = dict(job or {})
        payload = dict(job.get("payload") or {})
        instruction = payload.get("instruction") or ""

        payload["instruction"] = (
            str(instruction)
            + "\n\nRecovery instruction: Complete the task using bounded internal assumptions where safe. "
              "Explicitly label assumptions, unknowns, and validation steps. Do not block solely because "
              "additional external context is unavailable. Do not invent external facts or claim external actions."
        )
        payload["recovery_enriched"] = True
        payload["requires_approval"] = bool(payload.get("requires_approval", False))
        job["payload"] = payload
        return job
