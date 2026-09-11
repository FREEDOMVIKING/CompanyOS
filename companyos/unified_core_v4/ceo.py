from .util import stable_id, now

class CEOBrain:
    def __init__(self,db):
        self.db=db

    def rank_ventures(self):
        rows=[]
        for v in self.db.list_ventures():
            score=float(v.get("score",0) or 0)
            stage=str(v.get("stage") or "")
            stage_bonus=0
            if "READY" in stage.upper(): stage_bonus=8
            elif "GROW" in stage.upper(): stage_bonus=5
            elif "VALIDATE" in stage.upper(): stage_bonus=2
            priority=round(min(100,score+stage_bonus),2)
            rows.append({"venture_id":v["venture_id"],"name":v["name"],"base_score":score,"stage":stage,"executive_priority":priority})
        rows.sort(key=lambda x:x["executive_priority"],reverse=True)
        return rows

    def build_goals(self):
        ranked=self.rank_ventures()
        created=0
        if ranked:
            top=ranked[0]
            gid=stable_id("goal","top-venture",top["venture_id"])
            self.db.upsert_goal(gid,f"Advance {top['name']}",top["venture_id"],"ACTIVE",95,None,[],
                                {"reason":"Highest executive priority","score":top["executive_priority"]})
            created+=1
            for kind,title,prio,agent in [
                ("research","Strengthen market evidence",88,"research"),
                ("product","Improve offer and product readiness",84,"product"),
                ("marketing","Prepare acquisition strategy",80,"marketing"),
                ("finance","Validate venture economics",78,"finance"),
                ("launch","Assess launch readiness",76,"launch"),
            ]:
                sg=stable_id("goal",top["venture_id"],kind)
                self.db.upsert_goal(sg,title,top["venture_id"],"ACTIVE",prio,gid,[],
                                    {"agent":agent,"venture_name":top["name"],"kind":kind})
                created+=1
        return created

    def executive_decision(self):
        ranked=self.rank_ventures()
        if not ranked:
            return None
        top=ranked[0]
        if top["executive_priority"] >= 90:
            decision="ACCELERATE_VALIDATION"
            confidence=.90
            rationale="Top venture has strong internal priority but should continue through evidence and readiness gates."
        elif top["executive_priority"] >= 75:
            decision="FOCUS_AND_VALIDATE"
            confidence=.82
            rationale="Top venture is promising but still benefits from additional validation before external execution."
        else:
            decision="REASSESS_PORTFOLIO"
            confidence=.74
            rationale="Current venture scores do not justify aggressive execution."
        did=stable_id("decision",top["venture_id"],decision,top["stage"])
        self.db.record_decision(did,top["name"],decision,rationale,confidence,top)
        self.db.remember("executive_decision",top["name"],{"decision":decision,"rationale":rationale,"priority":top["executive_priority"]},.9)
        return {"decision_id":did,"subject":top["name"],"decision":decision,"confidence":confidence,"rationale":rationale}

    def plan(self):
        goals=self.build_goals()
        decision=self.executive_decision()
        return {"goals_created_or_refreshed":goals,"decision":decision,"ranked_ventures":self.rank_ventures(),"updated_at":now()}
