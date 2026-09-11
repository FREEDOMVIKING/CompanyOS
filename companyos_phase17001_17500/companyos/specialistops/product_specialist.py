from .base import BaseSpecialist
class ProductSpecialist(BaseSpecialist):
    def execute(self, job):
        p = job.get("payload", {})
        r = self.ask_ai(
            "You are CompanyOS product/build specialist. Produce implementable specs, dependencies, acceptance criteria, tests, risks, and rollback. Do not claim deployment.",
            {"instruction": p.get("instruction") or p, "success_criteria": p.get("success_criteria", [])}
        )
        return {"success": bool(r.get("success")), "capability":"product_specialist", "department":"product", "artifact_type":"implementation_spec", "analysis":r}
