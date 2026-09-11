from .base import BaseSpecialist
class ResearchSpecialist(BaseSpecialist):
    def execute(self, job):
        p = job.get("payload", {})
        r = self.ask_ai(
            "You are CompanyOS research specialist. Produce a rigorous internal research brief. Do not invent sources or claim web browsing unless source data is supplied. Label assumptions and unknowns. Return concrete validation steps.",
            {"instruction": p.get("instruction") or p, "success_criteria": p.get("success_criteria", [])}
        )
        return {"success": bool(r.get("success")), "capability":"research_specialist", "department":"research", "analysis":r, "verified_external_research":False}
