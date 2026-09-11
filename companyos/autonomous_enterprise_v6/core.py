from pathlib import Path
from .db import DB
from .migration import V5Migrator
from .provider import ProviderRouter
from .agents import AgentFactory
from .planner import EnterprisePlanner
from .executor import InternalExecutor
from .kpi import EnterpriseKPI
from .recovery import RecoveryAdvisor
from .util import now, atomic_write_json

class EnterpriseCoreV6:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/".companyos_enterprise_v6"
        self.runtime.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.runtime/"companyos_enterprise_v6.sqlite3")
        self.provider=ProviderRouter()
        self.migrator=V5Migrator(self.home,self.db)
        self.factory=AgentFactory(self.db)
        self.planner=EnterprisePlanner(self.db,self.provider)
        self.executor=InternalExecutor(self.db)
        self.kpi=EnterpriseKPI(self.db)
        self.recovery=RecoveryAdvisor(self.db)

    def migrate(self):
        return self.migrator.run()

    def run_cycle(self):
        migration=self.migrate()
        team_count=0
        for c in self.db.list_companies():
            team_count += self.factory.ensure_company_team(c)
        plans=self.planner.portfolio_plan()
        processed=self.executor.run()
        kpis=self.kpi.refresh()
        recovery=self.recovery.inspect()
        state=self.status()
        state.update({
            "migration":migration,
            "company_agents_refreshed":team_count,
            "company_plans":plans,
            "tasks_processed":processed,
            "kpis":kpis,
            "recovery":recovery,
            "cycle_completed_at":now()
        })
        self.db.set_kv("last_cycle",state)
        atomic_write_json(self.runtime/"status.json",state)
        return state

    def status(self):
        companies=self.db.list_companies()
        agents=self.db.list_agents()
        tasks=self.db.list_tasks(700)
        decisions=self.db.list_decisions(100)
        top=companies[0] if companies else None
        return {
            "status":"companyos_autonomous_enterprise_v6_ready",
            "companies_total":len(companies),
            "top_company":top.get("name") if top else None,
            "top_company_priority":top.get("priority") if top else 0,
            "agents_total":len(agents),
            "decisions_total":len(decisions),
            "provider":self.provider.status(),
            "tasks":{
                "queued":sum(t["status"]=="QUEUED" for t in tasks),
                "running":sum(t["status"]=="RUNNING" for t in tasks),
                "completed":sum(t["status"]=="COMPLETED" for t in tasks),
                "failed":sum(t["status"]=="FAILED" for t in tasks),
            },
            "external_actions":{
                "publication":False,
                "domain_purchases":False,
                "spending":False,
                "wallet_signing":False,
                "fund_transfers":False,
                "customer_outreach":False
            },
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
