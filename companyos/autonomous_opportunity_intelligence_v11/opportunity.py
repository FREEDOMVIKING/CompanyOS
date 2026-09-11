import json, re, math
from collections import defaultdict
from .util import sid, now, clamp, norm_text

STOP=set("""
the a an and or for of to in on with from by at is are be this that these those how why what
new best top using use your our their its into over under after before more less app ai
""".split())

class OpportunityBuilder:
    def __init__(self,db):
        self.db=db

    def _keywords(self,text):
        words=re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}",(text or "").lower())
        return [w for w in words if w not in STOP]

    def build(self):
        items=self.db.rows("SELECT * FROM research_items ORDER BY created_at DESC LIMIT 1000")
        if not items:
            return 0
        buckets=defaultdict(list)
        for item in items:
            words=self._keywords(item["title"]+" "+(item.get("summary") or ""))
            for w in set(words[:30]):
                buckets[(item.get("category") or "general",w)].append(item)

        created=0
        for (category,kw), group in buckets.items():
            if len(group)<2:
                continue
            evidence_count=len(group)
            demand=clamp(45 + min(40,evidence_count*7))
            margin=clamp(55 + (10 if category in ("technology","software","business") else 0))
            execution=clamp(70 if category in ("technology","software","business","general") else 60)
            strategic=clamp(65)
            evidence=clamp(35 + min(55,evidence_count*9))
            total=round(demand*.30 + margin*.20 + execution*.20 + strategic*.15 + evidence*.15,2)
            name=f"{kw.title()} Opportunity"
            oid=sid("opportunity",category,kw)
            status="EXECUTIVE_REVIEW" if total>=80 else "VALIDATE_MORE"
            payload={"keyword":kw,"sample_titles":[x["title"] for x in group[:6]]}
            self.db.exec("""INSERT OR REPLACE INTO opportunity_candidates
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (oid,name,category,status,demand,margin,execution,strategic,evidence,total,evidence_count,
             json.dumps(payload),now()))
            for item in group[:20]:
                eid=sid("evidence",oid,item["item_id"])
                self.db.exec("""INSERT OR IGNORE INTO evidence
                (evidence_id,opportunity_id,item_id,evidence_type,weight,payload_json,created_at)
                VALUES(?,?,?,'RESEARCH_SIGNAL',?,?,?)""",
                (eid,oid,item["item_id"],1.0,json.dumps({"title":item["title"],"url":item.get("url")}),now()))
            created+=1
        self.db.event("opportunity.build","opportunity_builder",{"candidates_refreshed":created})
        return created

    def queue_validation(self):
        n=0
        for o in self.db.rows("SELECT * FROM opportunity_candidates WHERE total_score>=65 ORDER BY total_score DESC LIMIT 50"):
            vid=sid("validation",o["opportunity_id"])
            hypothesis=f"Customers have a repeatable problem related to {o['name']} and will pay for a useful solution."
            self.db.exec("""INSERT OR REPLACE INTO validation_queue
            VALUES(?,?, 'QUEUED', ?, ?, ?, ?)""",
            (vid,o["opportunity_id"],int(round(o["total_score"])),hypothesis,
             json.dumps({"research_only":True,"external_side_effects":False}),now()))
            n+=1
        return n

    def handoff(self):
        n=0
        for o in self.db.rows("""SELECT * FROM opportunity_candidates
                                WHERE total_score>=80 AND evidence_count>=2
                                ORDER BY total_score DESC LIMIT 20"""):
            pid=sid("venture_proposal",o["opportunity_id"])
            rationale=f"Score {o['total_score']}/100 with {o['evidence_count']} research signals."
            self.db.exec("""INSERT OR REPLACE INTO venture_proposals
            VALUES(?,?,?,?,?,?,?,?)""",
            (pid,o["opportunity_id"],o["name"],"READY_FOR_EXECUTIVE_REVIEW",o["total_score"],
             rationale,json.dumps({"automatic_external_launch":False}),now()))
            n+=1
        return n
