from pathlib import Path
from .db import DB
from .migration import V11Migrator
from .generator import VentureGenerator
from .util import now

class AutonomousVentureGeneratorV12:
    def __init__(self,home):
        self.home=Path(home)
        self.run=self.home/".companyos_enterprise_v12"
        self.run.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.run/"companyos_enterprise_v12.sqlite3")
        self.migrator=V11Migrator(self.home,self.db)
        self.generator=VentureGenerator(self.db)

    def migrate(self):
        return self.migrator.run()

    def cycle(self):
        result={}
        result["migration"]=self.migrate()
        result["venture_proposals_refreshed"]=self.generator.build()
        result["business_plans_generated"]=self.generator.business_plans()
        result["milestones_generated"]=self.generator.milestones()
        result["launch_packages_generated"]=self.generator.launch_packages()
        result["executive_reviews_refreshed"]=self.generator.executive_queue()
        result["company_handoffs_refreshed"]=self.generator.handoff()
        result["status"]=self.status()
        self.db.event("cycle.completed","v12",result)
        return result

    def status(self):
        cs=self.db.rows("SELECT * FROM companies")
        ag=self.db.rows("SELECT * FROM agents")
        opp=self.db.rows("SELECT * FROM opportunities")
        vp=self.db.rows("SELECT * FROM venture_proposals")
        bp=self.db.rows("SELECT * FROM business_plans")
        ms=self.db.rows("SELECT * FROM milestones")
        lp=self.db.rows("SELECT * FROM launch_packages")
        er=self.db.rows("SELECT * FROM executive_review")
        ho=self.db.rows("SELECT * FROM company_handoffs")
        top=max(vp,key=lambda x:float(x["venture_score"] or 0)) if vp else None
        return {
            "status":"companyos_autonomous_venture_generator_v12_ready",
            "venture_generator":"ONLINE",
            "companies_total":len(cs),
            "agents_total":len(ag),
            "opportunities_total":len(opp),
            "venture_proposals_total":len(vp),
            "business_plans_total":len(bp),
            "milestones_total":len(ms),
            "launch_packages_total":len(lp),
            "executive_reviews_total":len(er),
            "company_handoffs_total":len(ho),
            "top_venture":top["name"] if top else None,
            "top_venture_score":top["venture_score"] if top else 0,
            "automatic_external_launch":False,
            "automatic_company_creation":False,
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
