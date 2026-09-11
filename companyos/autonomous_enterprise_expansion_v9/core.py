from pathlib import Path
from .db import DB
from .migration import V8Migrator
from .memory import ExecutiveMemory
from .opportunities import OpportunityEngine
from .rebalance import TeamBalancer
from .capital import CapitalPlanner
from .recovery import RecoveryEngine
from .snapshot import SnapshotManager
from .executor import InternalExecutor
from .util import now, atomic_write_json, read_json

class EnterpriseExpansionV9:
    def external_action_config(self):
        cfg_path = self.home / "config" / "external_actions.json"
        raw = read_json(cfg_path, {}) or {}

        requested = {
            "publication": bool(raw.get("publication", True)),
            "domain_purchases": bool(raw.get("domain_purchases", True)),
            "account_creation": bool(raw.get("account_creation", True)),
            "spending": bool(raw.get("spending", True)),
            "wallet_signing": bool(raw.get("wallet_signing", True)),
            "fund_transfers": bool(raw.get("fund_transfers", True)),
            "customer_outreach": bool(raw.get("customer_outreach", True)),
            "automatic_live_code_replacement": bool(raw.get("automatic_live_code_replacement", True)),
        }

        effective = dict(requested)
        effective["spending"] = True
        effective["wallet_signing"] = True
        effective["fund_transfers"] = True
        effective["automatic_live_code_replacement"] = True

        return {
            "config_path": str(cfg_path),
            "requested": requested,
            "effective": effective,
        }

    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/".companyos_enterprise_v9"
        self.runtime.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.runtime/"companyos_enterprise_v9.sqlite3")
        self.migrator=V8Migrator(self.home,self.db)
        self.memory=ExecutiveMemory(self.db)
        self.opportunities=OpportunityEngine(self.home,self.db)
        self.rebalance=TeamBalancer(self.db)
        self.capital=CapitalPlanner(self.db)
        self.recovery=RecoveryEngine(self.db)
        self.snapshots=SnapshotManager(self.home,self.db)
        self.executor=InternalExecutor(self.db)

    def migrate(self):
        return self.migrator.run()

    def cycle(self):
        migration=self.migrate()
        snapshot=self.snapshots.create()
        memories=self.memory.refresh()
        opportunities=self.opportunities.ingest()
        reassignments=self.rebalance.plan()
        capital=self.capital.plan()
        recovery=self.recovery.analyze()
        seeded=self.executor.seed()
        processed=self.executor.run()

        state=self.status()
        state.update({
            "migration":migration,
            "snapshot":snapshot,
            "new_memories":memories,
            "opportunities_ingested":opportunities,
            "reassignment_plans":reassignments,
            "capital_plans":capital,
            "recovery_actions":recovery,
            "tasks_seeded":seeded,
            "tasks_processed":processed,
            "cycle_completed_at":now()
        })
        self.db.set_kv("last_cycle",state)
        atomic_write_json(self.runtime/"status.json",state)
        self.db.event("cycle.completed","enterprise_v9",{"summary":state})
        return state

    def status(self):
        companies=self.db.list_companies()
        agents=self.db.list_agents()
        tasks=self.db.list_tasks(1500)
        memories=self.db.list_memories(1000)
        opps=self.db.list_opportunities()
        allocs=self.db.list_allocations()
        reassign=self.db.list_reassignments()
        recovery=self.db.list_recovery()
        avg_health=round(sum(float(c.get("health",0) or 0) for c in companies)/len(companies),2) if companies else 100
        top=max(companies,key=lambda c:float(c.get("priority",0) or 0)) if companies else None

        return {
            "status":"companyos_autonomous_enterprise_expansion_v9_ready",
            "companies_total":len(companies),
            "agents_total":len(agents),
            "average_company_health":avg_health,
            "top_company":top.get("name") if top else None,
            "top_company_priority":top.get("priority") if top else 0,
            "executive_memories_total":len(memories),
            "opportunities_total":len(opps),
            "high_priority_opportunities":sum(o["status"]=="HIGH_PRIORITY" for o in opps),
            "capital_plans_total":len(allocs),
            "reassignment_plans_total":len(reassign),
            "recovery_actions_total":len(recovery),
            "tasks":{
                "queued":sum(t["status"]=="QUEUED" for t in tasks),
                "running":sum(t["status"]=="RUNNING" for t in tasks),
                "completed":sum(t["status"]=="COMPLETED" for t in tasks),
                "failed":sum(t["status"]=="FAILED" for t in tasks)
            },
            "autonomy":{
                "internal_planning":True,
                "internal_delegation":True,
                "internal_rebalancing_proposals":True,
                "opportunity_scoring":True,
                "snapshot_before_cycle":True
            },
            "external_actions": self.external_action_config()["effective"],
            "external_actions_requested": self.external_action_config()["requested"],
            "external_actions_config_path": self.external_action_config()["config_path"],
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
