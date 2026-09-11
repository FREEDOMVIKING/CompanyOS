from pathlib import Path
from .db import DB
from .migration import V12Migrator
from .builder import CompanyBuilder
from .util import now

class AutonomousCompanyBuilderV13:
    def __init__(self,home):
        self.home=Path(home)
        self.run=self.home/".companyos_enterprise_v13"
        self.run.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.run/"companyos_enterprise_v13.sqlite3")
        self.migrator=V12Migrator(self.home,self.db)
        self.builder=CompanyBuilder(self.home,self.db)

    def migrate(self):
        return self.migrator.run()

    def cycle(self):
        result={}
        result["migration"]=self.migrate()
        result["launch_queue_refreshed"]=self.builder.board_select()
        result["companies_built"]=self.builder.build_companies()
        result["lifecycle_refreshed"]=self.builder.lifecycle_refresh()
        result["reinvestment_refreshed"]=self.builder.reinvestment_refresh()
        result["status"]=self.status()
        self.db.event("cycle.completed","v13",result)
        return result

    def status(self):
        cs=self.db.rows("SELECT * FROM companies")
        ag=self.db.rows("SELECT * FROM agents")
        h=self.db.rows("SELECT * FROM venture_handoffs")
        q=self.db.rows("SELECT * FROM launch_queue")
        b=self.db.rows("SELECT * FROM company_builds")
        p=self.db.rows("SELECT * FROM products")
        c=self.db.rows("SELECT * FROM campaigns")
        s=self.db.rows("SELECT * FROM sales_plans")
        l=self.db.rows("SELECT * FROM lifecycle")
        r=self.db.rows("SELECT * FROM reinvestment_recommendations")
        rev=self.db.rows("SELECT COALESCE(SUM(amount),0) AS total FROM revenue_ledger WHERE verified=1")[0]["total"]
        top=max(l,key=lambda x:float(x["growth_score"] or 0)) if l else None
        return {
            "status":"companyos_autonomous_company_builder_v13_ready",
            "company_builder":"ONLINE",
            "legacy_companies_total":len(cs),
            "agents_total":len(ag),
            "venture_handoffs_total":len(h),
            "launch_queue_total":len(q),
            "local_company_builds_total":len(b),
            "products_total":len(p),
            "marketing_campaigns_total":len(c),
            "sales_plans_total":len(s),
            "lifecycle_records_total":len(l),
            "reinvestment_recommendations_total":len(r),
            "verified_revenue":float(rev or 0),
            "top_growth_company_id":top["company_id"] if top else None,
            "top_growth_score":top["growth_score"] if top else 0,
            "automatic_external_publish":True,
            "automatic_domain_purchase":True,
            "automatic_account_creation":True,
            "automatic_spending":True,
            "automatic_fund_transfers":False,
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
