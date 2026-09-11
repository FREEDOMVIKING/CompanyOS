from pathlib import Path
from .db import DB
from .migration import Migrator
from .plugins import PluginManager
from .agents import register as register_agents
from .portfolio import PortfolioEngine
from .kpi import KPIEngine
from .forecast import ForecastEngine
from .ceo import CEOBrain
from .delegation import Delegator
from .recovery import RecoveryManager
from .executor import InternalExecutor
from .util import now, atomic_write_json

class UnifiedCoreV5:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/".companyos_unified_v5"
        self.runtime.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.runtime/"companyos_unified_v5.sqlite3")
        register_agents(self.db)
        self.plugins=PluginManager(self.home,self.db)
        self.plugins.discover()
        self.migrator=Migrator(self.home,self.db)
        self.portfolio=PortfolioEngine(self.db)
        self.kpi=KPIEngine(self.db)
        self.forecast=ForecastEngine(self.db)
        self.ceo=CEOBrain(self.db,self.portfolio)
        self.delegator=Delegator(self.db,self.plugins)
        self.recovery=RecoveryManager(self.db)
        self.executor=InternalExecutor(self.db)

    def migrate(self): return self.migrator.run()
    def reload_plugins(self): return {"discovered":self.plugins.discover(),"plugins_total":len(self.db.list_plugins())}

    def run_cycle(self):
        migration=self.migrate()
        companies=self.portfolio.ensure_companies()
        plan=self.ceo.plan()
        delegated=self.delegator.assign()
        processed=self.executor.run()
        kpis=self.kpi.refresh()
        forecast=self.forecast.forecast()
        health=self.recovery.health()
        state=self.status()
        state.update({"migration":migration,"companies_refreshed":companies,"executive_plan":plan,
                      "delegated_tasks":delegated,"tasks_processed":processed,
                      "kpis":kpis,"forecast":forecast,"health":health,"cycle_completed_at":now()})
        self.db.set_kv("last_cycle",state)
        atomic_write_json(self.runtime/"status.json",state)
        return state

    def status(self):
        modules=self.db.list_modules()
        ventures=self.db.list_ventures()
        companies=self.db.list_companies()
        agents=self.db.list_agents()
        plugins=self.db.list_plugins()
        tasks=self.db.list_tasks(500)
        goals=self.db.list_goals()
        health=self.db.get_kv("health_report",{}) or {}
        forecast=self.db.get_kv("revenue_forecast",{}) or {}
        decisions=self.db.list_decisions(25)
        top=ventures[0] if ventures else None
        latest=decisions[0] if decisions else None
        return {
            "status":"companyos_unified_core_v5_ready",
            "foundation":"FINAL_ARCHITECTURAL_FOUNDATION",
            "health_percent":health.get("health_percent",100.0),
            "modules_total":len(modules),
            "companies_total":len(companies),
            "ventures_total":len(ventures),
            "top_venture":top.get("name") if top else None,
            "top_venture_score":top.get("score") if top else 0,
            "agents_total":len(agents),
            "plugins_total":len(plugins),
            "goals_total":len(goals),
            "latest_executive_decision":latest.get("decision") if latest else None,
            "forecast":forecast,
            "tasks":{
                "queued":sum(t["status"]=="QUEUED" for t in tasks),
                "running":sum(t["status"]=="RUNNING" for t in tasks),
                "completed":sum(t["status"]=="COMPLETED" for t in tasks),
                "failed":sum(t["status"]=="FAILED" for t in tasks)
            },
            "external_actions":{
                "publication":False,"spending":False,"wallet_signing":False,
                "fund_transfers":False,"customer_outreach":False,"domain_purchases":False
            },
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
