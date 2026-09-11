from .base import BaseSpecialist
class GrowthSpecialist(BaseSpecialist):
    def execute(self, job):
        p = job.get("payload", {})
        r = self.ask_ai(
            "You are CompanyOS growth specialist. Design measurable low-risk experiments with metrics, expected value, effort, risk, stop criteria, and learning loop. Do not spend money or send messages.",
            {"instruction": p.get("instruction") or p, "success_criteria": p.get("success_criteria", [])}
        )
        return {"success": bool(r.get("success")), "capability":"growth_specialist", "department":"growth", "analysis":r, "external_action_taken":False}
