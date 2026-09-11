from pathlib import Path
from .db import DB
from .migration import Migrator
from .bus import EventBus
from .plugins import register_builtin_plugins, discover_legacy_plugins
from .agents import register_agents, AgentRunner
from .scheduler import Scheduler
from .health import HealthManager
from .util import stable_id, now, atomic_write_json

class UnifiedCoreV3:
    def __init__(self, home):
        self.home=Path(home)
        self.runtime=self.home/".companyos_unified_v3"
        self.runtime.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.runtime/"companyos_unified_v3.sqlite3")
        self.bus=EventBus(self.db)
        register_agents(self.db)
        register_builtin_plugins(self.db)
        discover_legacy_plugins(self.home,self.db)
        self.migrator=Migrator(self.home,self.db)
        self.scheduler=Scheduler(self.db)
        self.scheduler.ensure_defaults()
        self.health=HealthManager(self.db,self.bus)
        self.agent_runner=AgentRunner(self.db,self.bus)

    def migrate(self):
        return self.migrator.run()

    def seed_dynamic_tasks(self):
        ventures=self.db.list_ventures()
        for v in ventures[:5]:
            if float(v.get("score",0) or 0) >= 70:
                self.db.add_task(stable_id("launch",v["venture_id"],v.get("stage")),
                                 "launch_readiness",
                                 f"Review launch readiness: {v['name']}",75,"launch",
                                 {"venture_id":v["venture_id"],"venture_name":v["name"],"score":v.get("score"),"stage":v.get("stage")})

    def run_tasks(self, limit=12):
        done=0
        for t in self.db.next_tasks(limit):
            self.db.task_state(t["task_id"],"RUNNING",1)
            try:
                self.agent_runner.run(t)
                self.db.task_state(t["task_id"],"COMPLETED")
            except Exception as e:
                self.bus.publish("task.error","core",{"task_id":t["task_id"],"error":str(e)})
                self.db.task_state(t["task_id"],"FAILED")
                self.db.requeue_failed(t["task_id"])
            done+=1
        return done

    def run_cycle(self):
        migration=self.migrate()
        modules=self.db.list_modules()
        ventures=self.db.list_ventures()
        plugins=self.db.list_plugins()
        scheduled=self.scheduler.enqueue_due({"module_count":len(modules),"venture_count":len(ventures),"plugin_count":len(plugins)})
        self.seed_dynamic_tasks()
        processed=self.run_tasks()
        health=self.health.inspect()
        state=self.status()
        state.update({"migration":migration,"scheduled_created":scheduled,"tasks_processed":processed,"health":health,"cycle_completed_at":now()})
        self.db.set_kv("last_cycle",state)
        atomic_write_json(self.runtime/"status.json",state)
        return state

    def status(self):
        modules=self.db.list_modules()
        ventures=self.db.list_ventures()
        agents=self.db.list_agents()
        plugins=self.db.list_plugins()
        tasks=self.db.list_tasks(300)
        health=self.db.get_kv("health_report",{}) or {}
        top=ventures[0] if ventures else None
        return {
            "status":"companyos_unified_core_v3_ready",
            "health_percent":health.get("health_percent",100.0),
            "modules_total":len(modules),
            "ventures_total":len(ventures),
            "top_venture":top.get("name") if top else None,
            "top_venture_score":top.get("score") if top else 0,
            "agents_total":len(agents),
            "plugins_total":len(plugins),
            "tasks":{
                "queued":sum(t["status"]=="QUEUED" for t in tasks),
                "running":sum(t["status"]=="RUNNING" for t in tasks),
                "completed":sum(t["status"]=="COMPLETED" for t in tasks),
                "failed":sum(t["status"]=="FAILED" for t in tasks),
                "dead":sum(t["status"]=="DEAD" for t in tasks),
            },
            "external_actions":{
                "publication":False,"spending":False,"wallet_signing":False,
                "fund_transfers":False,"customer_outreach":False,"domain_purchases":False
            },
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
