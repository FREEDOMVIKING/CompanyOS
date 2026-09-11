from pathlib import Path
from .db import StateDB
from .migration import LegacyMigrator
from .agents import register_defaults, AgentRunner
from .orchestrator import Orchestrator
from .util import now, atomic_write_json

class UnifiedCore:
    def __init__(self, home):
        self.home = Path(home)
        self.runtime = self.home / ".companyos_unified_v2"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.db = StateDB(self.runtime / "companyos_unified_v2.sqlite3")
        register_defaults(self.db)
        self.migrator = LegacyMigrator(self.home, self.db)
        self.agent_runner = AgentRunner(self.db)
        self.orchestrator = Orchestrator(self)

    def migrate(self):
        return self.migrator.run()

    def run_cycle(self):
        migration = self.migrate()
        self.orchestrator.create_tasks()
        processed = self.orchestrator.execute_tasks()
        state = self.status()
        state["tasks_processed_this_cycle"] = processed
        state["migration"] = migration
        state["cycle_completed_at"] = now()
        self.db.set_kv("last_cycle", state)
        atomic_write_json(self.runtime / "status.json", state)
        return state

    def status(self):
        modules = self.db.list_modules()
        ventures = self.db.list_ventures()
        tasks = self.db.list_tasks(200)
        agents = self.db.list_agents()
        healthy = sum(int(m.get("healthy",0)) for m in modules)
        queued = sum(t.get("status") == "QUEUED" for t in tasks)
        running = sum(t.get("status") == "RUNNING" for t in tasks)
        failed = sum(t.get("status") == "FAILED" for t in tasks)
        completed = sum(t.get("status") == "COMPLETED" for t in tasks)
        top = ventures[0] if ventures else None

        health_pct = round((healthy / len(modules) * 100), 1) if modules else 100.0
        return {
            "status":"companyos_unified_core_ready",
            "health_percent":health_pct,
            "modules_total":len(modules),
            "modules_healthy":healthy,
            "ventures_total":len(ventures),
            "top_venture": top.get("name") if top else None,
            "top_venture_score": top.get("score") if top else 0,
            "tasks":{"queued":queued,"running":running,"completed":completed,"failed":failed},
            "agents_total":len(agents),
            "external_actions":{
                "publication":False,
                "spending":False,
                "wallet_signing":False,
                "fund_transfers":False,
                "customer_outreach":False,
                "domain_purchases":False,
            },
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now(),
        }
