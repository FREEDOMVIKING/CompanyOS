from .util import stable_id

class DebateEngine:
    def __init__(self,db):
        self.db=db

    def critique_top_plan(self):
        ventures=self.db.list_ventures()
        if not ventures: return None
        v=ventures[0]
        weaknesses=[]
        if float(v.get("score",0) or 0) < 90: weaknesses.append("internal score below 90")
        stage=str(v.get("stage") or "")
        if "READY" not in stage.upper(): weaknesses.append("not yet fully launch-ready")
        result={
            "venture_id":v["venture_id"],"venture_name":v["name"],
            "critic_position":"PROCEED_CAUTIOUSLY" if weaknesses else "SUPPORT",
            "weaknesses":weaknesses,
            "recommendation":"Resolve evidence/readiness gaps before irreversible external execution." if weaknesses else "Continue controlled preparation."
        }
        self.db.remember("critic_review",v["name"],result,.8)
        self.db.event("executive.critique","critic",result,target="ceo")
        return result
