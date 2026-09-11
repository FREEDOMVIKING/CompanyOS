from pathlib import Path
from .db import DB
from .migration import Migrator
from .plugins import register as register_plugins
from .agents import register as register_agents
from .ceo import CEOBrain
from .delegation import Delegator
from .debate import DebateEngine
from .executor import InternalExecutor
from .util import now, atomic_write_json

class UnifiedCoreV4:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/".companyos_unified_v4"
        self.runtime.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.runtime/"companyos_unified_v4.sqlite3")
        register_plugins(self.db); register_agents(self.db)
        self.migrator=Migrator(self.home,self.db)
        self.ceo=CEOBrain(self.db)
        self.delegator=Delegator(self.db)
        self.debate=DebateEngine(self.db)
        self.executor=InternalExecutor(self.db)

    def migrate(self): return self.migrator.run()

    def run_cycle(self):
        migration=self.migrate()
        plan=self.ceo.plan()
        delegated=self.delegator.delegate_goals()
        critique=self.debate.critique_top_plan()
        processed=self.executor.run_tasks()
        state=self.status()
        state.update({"migration":migration,"executive_plan":plan,"delegated_tasks":delegated,
                      "critic_review":critique,"tasks_processed":processed,"cycle_completed_at":now()})
        self.db.set_kv("last_cycle",state)
        atomic_write_json(self.runtime/"status.json",state)
        return state

    def status(self):
        modules=self.db.list_modules()
        ventures=self.db.list_ventures()
        agents=self.db.list_agents()
        plugins=self.db.list_plugins()
        tasks=self.db.list_tasks(400)
        goals=self.db.list_goals()
        decisions=self.db.list_decisions(50)
        memories=self.db.list_memories(50)
        healthy=sum(int(m.get("healthy",0)) for m in modules)
        health=round((healthy/len(modules)*100),1) if modules else 100.0
        top=ventures[0] if ventures else None
        latest=decisions[0] if decisions else None
        return {
            "status":"companyos_unified_core_v4_ready",
            "health_percent":health,
            "modules_total":len(modules),
            "ventures_total":len(ventures),
            "top_venture":top.get("name") if top else None,
            "top_venture_score":top.get("score") if top else 0,
            "agents_total":len(agents),
            "plugins_total":len(plugins),
            "goals_total":len(goals),
            "memories_total":len(memories),
            "latest_executive_decision":latest.get("decision") if latest else None,
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
            "dashboard_url":"http://127.0.0.1:9000","updated_at":now()
        }
