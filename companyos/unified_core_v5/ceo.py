from .util import stable_id, now

class CEOBrain:
    def __init__(self,db,portfolio):
        self.db=db; self.portfolio=portfolio

    def plan(self):
        ranked=self.portfolio.rank()
        if not ranked:
            return {"status":"NO_VENTURES","goals":0,"decision":None}

        top=ranked[0]
        root=stable_id("goal","portfolio",top["venture_id"])
        self.db.upsert_goal(root,f"Advance {top['name']}",top["venture_id"],top.get("company_id"),
                            "ACTIVE",95,None,[],{"executive_priority":top["executive_priority"]})

        subgoals=[
            ("research","Strengthen evidence",88,"research"),
            ("product","Improve product readiness",84,"product"),
            ("marketing","Prepare acquisition strategy",82,"marketing"),
            ("finance","Validate economics",80,"finance"),
            ("operations","Prepare operating workflow",78,"operations"),
            ("launch","Assess launch readiness",76,"launch"),
        ]
        for kind,title,priority,agent in subgoals:
            gid=stable_id("goal",top["venture_id"],kind)
            self.db.upsert_goal(gid,title,top["venture_id"],top.get("company_id"),"ACTIVE",priority,root,[],
                                {"kind":kind,"agent":agent,"venture_name":top["name"]})

        if top["executive_priority"]>=90:
            decision="ACCELERATE_VALIDATION"
            confidence=.90
        elif top["executive_priority"]>=75:
            decision="FOCUS_AND_VALIDATE"
            confidence=.84
        else:
            decision="REASSESS_PORTFOLIO"
            confidence=.72

        rationale=f"{top['name']} is currently the highest-ranked venture at {top['executive_priority']} executive priority."
        did=stable_id("decision",top["venture_id"],decision,top.get("stage"))
        self.db.record_decision(did,top["name"],decision,rationale,confidence,top)
        self.db.remember("executive_decision",top["name"],{"decision":decision,"rationale":rationale},.95)
        return {"status":"PLANNED","top_venture":top["name"],"decision":decision,"confidence":confidence,"updated_at":now()}
