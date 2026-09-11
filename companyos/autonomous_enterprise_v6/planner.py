from .util import stable_id, now

class EnterprisePlanner:
    def __init__(self,db,provider):
        self.db=db
        self.provider=provider

    def plan_company(self,company):
        cid=company["company_id"]
        priority=float(company.get("priority") or 0)
        if priority>=90:
            decision="ACCELERATE_VALIDATION"
            confidence=.90
        elif priority>=75:
            decision="FOCUS_AND_VALIDATE"
            confidence=.84
        else:
            decision="DEVELOP_AND_REASSESS"
            confidence=.75

        rationale=f"{company['name']} has enterprise priority {priority:.2f}."
        did=stable_id("enterprise-decision",cid,decision)
        self.db.record_decision(did,cid,company["name"],decision,rationale,confidence,company)

        plan=[
            ("research","Strengthen market evidence",92),
            ("product","Improve product readiness",88),
            ("marketing","Build acquisition plan",84),
            ("finance","Validate unit economics",82),
            ("operations","Prepare operating workflow",80),
            ("launch","Assess launch readiness",78),
            ("critic","Challenge current plan",76),
        ]
        for specialist,title,prio in plan:
            aid=stable_id(cid,specialist)
            tid=stable_id("enterprise-task",cid,specialist)
            self.db.add_task(tid,cid,"company_workstream",title,prio,aid,{
                "company_id":cid,
                "company_name":company["name"],
                "specialist":specialist,
                "executive_decision":decision
            })

        return {
            "company_id":cid,
            "company_name":company["name"],
            "decision":decision,
            "confidence":confidence,
            "provider_summary":self.provider.executive_summary(company),
            "updated_at":now()
        }

    def portfolio_plan(self):
        companies=self.db.list_companies()
        return [self.plan_company(c) for c in companies]
