from .base import BaseSpecialist
class FinanceSpecialist(BaseSpecialist):
    def execute(self, job):
        p = job.get("payload", {})
        r = self.ask_ai(
            "You are CompanyOS finance analyst. Perform scenario analysis, unit economics, sensitivity analysis, and explicit uncertainty. Never initiate transfers or spending.",
            {"instruction": p.get("instruction") or p, "success_criteria": p.get("success_criteria", []), "mode":"analysis_only"}
        )
        return {"success": bool(r.get("success")), "capability":"finance_specialist", "department":"finance", "analysis":r, "transaction_executed":False}
