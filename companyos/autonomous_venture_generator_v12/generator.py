import json
from .util import sid, now

class VentureGenerator:
    def __init__(self,db):
        self.db=db

    def _model_for(self,category,name):
        c=(category or "").lower()
        n=(name or "").lower()
        if any(k in c+n for k in ("software","technology","automation","ai")):
            return "SaaS / productized software", "subscription + setup/service revenue"
        if any(k in c+n for k in ("business","service","contractor","local")):
            return "productized service", "project fee + recurring service plan"
        if any(k in c+n for k in ("education","template","content")):
            return "digital product", "one-time purchase + premium bundle"
        return "lean digital service", "service fee + recurring support"

    def _startup_costs(self,business_model):
        if "SaaS" in business_model:
            return 300, 2500
        if "productized service" in business_model:
            return 150, 1200
        if "digital product" in business_model:
            return 50, 700
        return 100, 1000

    def _risk(self,score,evidence):
        if score>=85 and evidence>=4:
            return "LOW_TO_MODERATE"
        if score>=72:
            return "MODERATE"
        return "HIGH"

    def build(self):
        created=0
        for o in self.db.rows("SELECT * FROM opportunities WHERE total_score>=65 ORDER BY total_score DESC"):
            business_model,revenue_model=self._model_for(o["category"],o["name"])
            low,high=self._startup_costs(business_model)
            risk=self._risk(float(o["total_score"] or 0),int(o["evidence_count"] or 0))

            venture_score=round(
                float(o["total_score"] or 0)*0.75 +
                (85 if risk=="LOW_TO_MODERATE" else 75 if risk=="MODERATE" else 60)*0.25,
                2
            )
            pid=sid("proposal",o["opportunity_id"])
            rationale=f"Opportunity score {o['total_score']}/100 with {o['evidence_count']} evidence signals."
            status="READY_FOR_PLAN" if venture_score>=70 else "HOLD_AND_VALIDATE"

            self.db.exec("""INSERT OR REPLACE INTO venture_proposals
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (pid,o["opportunity_id"],o["name"],o["category"],status,
             float(o["total_score"] or 0),venture_score,business_model,revenue_model,
             low,high,risk,rationale,json.dumps({"external_side_effects":False}),now()))
            created+=1
        self.db.event("venture_generator.build","venture_generator",{"proposals_refreshed":created})
        return created

    def business_plans(self):
        n=0
        for p in self.db.rows("SELECT * FROM venture_proposals WHERE status IN ('READY_FOR_PLAN','PLAN_GENERATED')"):
            plan_id=sid("business_plan",p["proposal_id"])
            problem=f"Target customers need a simpler, faster solution related to {p['name']}."
            customer=f"Early adopters with a clear recurring problem in the {p['category']} market."
            offer=f"A focused {p['business_model']} built around the strongest validated use case."
            differentiation="Fast implementation, narrow positioning, measurable outcomes, and iterative validation."
            gtm="Start with direct outreach to a tightly defined niche, then expand into repeatable inbound channels."
            operations="Use specialist agents for research, product, sales, support, and weekly KPI review."
            kpis=["qualified_leads","conversion_rate","time_to_value","gross_margin","retention","customer_feedback_score"]

            self.db.exec("""INSERT OR REPLACE INTO business_plans
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (plan_id,p["proposal_id"],problem,customer,offer,differentiation,gtm,operations,
             json.dumps(kpis),json.dumps({"generated_by":"CompanyOS V12"}),now()))
            self.db.exec("UPDATE venture_proposals SET status='PLAN_GENERATED',updated_at=? WHERE proposal_id=?",
                         (now(),p["proposal_id"]))
            n+=1
        return n

    def milestones(self):
        n=0
        template=[
            (1,"Validate customer pain","At least 5 credible validation signals or interviews."),
            (2,"Define minimum viable offer","One clear offer, price, target user, and outcome."),
            (3,"Build MVP or service prototype","Usable first version exists and can be demonstrated."),
            (4,"Acquire first prospects","Qualified prospect list and outreach plan are ready."),
            (5,"Launch controlled pilot","Pilot can run with measurable KPI tracking."),
            (6,"Review economics","Costs, gross margin, conversion, and retention assumptions reviewed.")
        ]
        for p in self.db.rows("SELECT * FROM venture_proposals WHERE status='PLAN_GENERATED'"):
            for seq,title,criteria in template:
                mid=sid("milestone",p["proposal_id"],seq)
                self.db.exec("""INSERT OR REPLACE INTO milestones VALUES(?,?,?,?,?,?,?,?)""",
                             (mid,p["proposal_id"],seq,title,criteria,"QUEUED",
                              json.dumps({"external_side_effects":False}),now()))
                n+=1
        return n

    def launch_packages(self):
        n=0
        for p in self.db.rows("SELECT * FROM venture_proposals WHERE status='PLAN_GENERATED'"):
            milestones=self.db.rows("SELECT * FROM milestones WHERE proposal_id=? ORDER BY sequence_no",(p["proposal_id"],))
            checklist=[
                "Business plan complete",
                "Revenue model selected",
                "Startup cost range estimated",
                "Risk assessment complete",
                "Milestones generated",
                "Pilot KPI set defined",
                "External launch requires separate approval"
            ]
            readiness=min(100, round(float(p["venture_score"] or 0)*0.85 + (15 if len(milestones)>=6 else 5),2))
            lid=sid("launch",p["proposal_id"])
            self.db.exec("""INSERT OR REPLACE INTO launch_packages VALUES(?,?,?,?,?,?,?,?)""",
                         (lid,p["proposal_id"],"READY_FOR_EXECUTIVE_REVIEW",readiness,
                          json.dumps(checklist),json.dumps({"generated_assets":["business_plan","milestones","launch_checklist"]}),
                          json.dumps({"automatic_external_launch":False}),now()))
            n+=1
        return n

    def executive_queue(self):
        n=0
        for lp in self.db.rows("""SELECT l.*,p.name,p.venture_score,p.risk_level
                                 FROM launch_packages l JOIN venture_proposals p ON p.proposal_id=l.proposal_id
                                 WHERE l.status='READY_FOR_EXECUTIVE_REVIEW'"""):
            rid=sid("review",lp["proposal_id"])
            priority=int(round(float(lp["launch_score"] or 0)))
            recommendation="ADVANCE_TO_CONTROLLED_PILOT" if priority>=78 else "VALIDATE_MORE"
            self.db.exec("""INSERT OR REPLACE INTO executive_review VALUES(?,?,?,?,?,?,?)""",
                         (rid,lp["proposal_id"],"PENDING",priority,recommendation,
                          json.dumps({"risk_level":lp["risk_level"],"external_launch_enabled":False}),now()))
            n+=1
        return n

    def handoff(self):
        n=0
        for r in self.db.rows("""SELECT r.*,p.name FROM executive_review r
                                JOIN venture_proposals p ON p.proposal_id=r.proposal_id
                                WHERE r.recommendation='ADVANCE_TO_CONTROLLED_PILOT'"""):
            hid=sid("handoff",r["proposal_id"])
            company_name=r["name"].replace(" Opportunity","").strip() or "New Venture"
            self.db.exec("""INSERT OR REPLACE INTO company_handoffs VALUES(?,?,?,?,?,?)""",
                         (hid,r["proposal_id"],"READY_FOR_COMPANY_CREATION_REVIEW",company_name,
                          json.dumps({"company_created":False,"external_side_effects":False}),now()))
            n+=1
        return n
