import json
from pathlib import Path
from .db import DB
from .migration import V10Migrator
from .sources import SourceRegistry
from .research import ResearchEngine
from .opportunity import OpportunityBuilder
from .util import now

class OpportunityIntelligenceV11:
    def __init__(self,home):
        self.home=Path(home)
        self.run=self.home/".companyos_enterprise_v11"
        self.run.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.run/"companyos_enterprise_v11.sqlite3")
        self.migrator=V10Migrator(self.home,self.db)
        self.sources=SourceRegistry(self.home,self.db)
        self.research=ResearchEngine(self.db,self.sources)
        self.builder=OpportunityBuilder(self.db)

    def migrate(self):
        return self.migrator.run()

    def cycle(self):
        result={}
        result["migration"]=self.migrate()
        result["sources_synced"]=self.sources.sync()
        result["research"]=self.research.cycle()
        result["opportunities_refreshed"]=self.builder.build()
        result["validation_queued"]=self.builder.queue_validation()
        result["venture_proposals_refreshed"]=self.builder.handoff()
        result["status"]=self.status()
        self.db.event("cycle.completed","v11",result)
        return result

    def status(self):
        cs=self.db.rows("SELECT * FROM companies")
        ag=self.db.rows("SELECT * FROM agents")
        sources=self.db.rows("SELECT * FROM research_sources")
        items=self.db.rows("SELECT * FROM research_items")
        opps=self.db.rows("SELECT * FROM opportunity_candidates")
        vals=self.db.rows("SELECT * FROM validation_queue")
        props=self.db.rows("SELECT * FROM venture_proposals")
        top=max(opps,key=lambda x:float(x["total_score"] or 0)) if opps else None
        return {
            "status":"companyos_autonomous_opportunity_intelligence_v11_ready",
            "opportunity_intelligence":"ONLINE",
            "companies_total":len(cs),
            "agents_total":len(ag),
            "research_sources_total":len(sources),
            "research_sources_enabled":sum(bool(x["enabled"]) for x in sources),
            "research_sources_healthy":sum(x["status"]=="OK" for x in sources),
            "research_items_total":len(items),
            "opportunities_total":len(opps),
            "executive_review_opportunities":sum(x["status"]=="EXECUTIVE_REVIEW" for x in opps),
            "validation_queue_total":len(vals),
            "venture_proposals_total":len(props),
            "top_opportunity":top["name"] if top else None,
            "top_opportunity_score":top["total_score"] if top else 0,
            "continuous_research":True,
            "automatic_external_launch":False,
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
