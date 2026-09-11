from .base import BaseSpecialist
class OperationsSpecialist(BaseSpecialist):
    def execute(self, job):
        p = job.get("payload", {})
        r = self.ask_ai(
            "You are CompanyOS operations specialist. Produce SOPs, readiness checks, incident response, dependency validation, and rollback plans. Do not deploy to production without approval.",
            {"instruction": p.get("instruction") or p, "success_criteria": p.get("success_criteria", [])}
        )
        return {"success": bool(r.get("success")), "capability":"operations_specialist", "department":"operations", "analysis":r, "production_changed":False}
