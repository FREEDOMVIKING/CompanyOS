class DiagnosticEngine:
    def diagnose(self, job, execution, verification=None):
        execution = execution or {}
        verification = verification or {}
        text = " ".join([
            str(execution.get("error","")),
            str(execution.get("reason","")),
            str(execution.get("message","")),
            str(execution.get("analysis","")),
        ]).lower()

        if verification.get("passed") is True:
            return {"kind":"resolved","recoverable":False}

        if any(x in text for x in [
            "need more information",
            "missing input",
            "insufficient context",
            "please provide details",
            "required field",
        ]):
            return {"kind":"missing_input","recoverable":True}

        if any(x in text for x in [
            "timeout","temporar","connection","network","provider","rate limit"
        ]):
            return {"kind":"transient_failure","recoverable":True}

        if execution.get("blocked") or execution.get("requires_approval"):
            return {"kind":"approval_required","recoverable":False}

        return {"kind":"execution_failure","recoverable":True}
