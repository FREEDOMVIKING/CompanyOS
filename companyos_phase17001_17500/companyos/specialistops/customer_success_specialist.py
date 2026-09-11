from .base import BaseSpecialist
class CustomerSuccessSpecialist(BaseSpecialist):
    def execute(self, job):
        p = job.get("payload", {})
        r = self.ask_ai(
            "You are CompanyOS customer success specialist. Analyze onboarding, retention, support friction, feedback themes, and recommended internal improvements. Do not contact customers automatically.",
            {"instruction": p.get("instruction") or p, "success_criteria": p.get("success_criteria", [])}
        )
        return {"success": bool(r.get("success")), "capability":"customer_success_specialist", "department":"customer_success", "analysis":r, "external_message_sent":False}
