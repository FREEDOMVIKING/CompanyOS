from pathlib import Path
from .db import DB
from .migration import V15Migrator
from .connectors import ConnectorManager
from .executor import ActionExecutor
from .util import now

class ActionControlExecutionV16:
    def __init__(self,home):
        self.home=Path(home); self.run=self.home/".companyos_enterprise_v16"
        self.run.mkdir(parents=True,exist_ok=True)
        self.db=DB(self.run/"companyos_enterprise_v16.sqlite3")
        self.migrator=V15Migrator(self.home,self.db)
        self.connectors=ConnectorManager(self.home,self.db)
        self.executor=ActionExecutor(self.db,self.connectors)
    def migrate(self): return self.migrator.run()
    def cycle(self):
        return {
            "migration":self.migrate(),
            "connectors_synced":self.connectors.sync(),
            "connector_health":self.connectors.health(),
            "policy_review":self.executor.review_all(),
            "execution":self.executor.execute(),
            "status":self.status()
        }
    def status(self):
        cs=self.db.rows("SELECT * FROM connectors"); acts=self.db.rows("SELECT * FROM actions")
        return {
            "status":"companyos_action_control_execution_v16_ready",
            "action_control_execution":"ONLINE",
            "company_builds_total":len(self.db.rows("SELECT * FROM company_builds")),
            "connectors_total":len(cs),
            "connectors_configured":sum(x["status"] in ("CONFIGURED","HEALTHY") for x in cs),
            "connectors_healthy":sum(x["status"]=="HEALTHY" for x in cs),
            "actions_total":len(acts),
            "actions_review_required":sum(x["status"]=="REVIEW_REQUIRED" for x in acts),
            "actions_approved":sum(x["status"]=="APPROVED" for x in acts),
            "actions_executed":sum(x["status"]=="EXECUTED" for x in acts),
            "actions_failed":sum(x["status"] in ("FAILED","HTTP_ERROR","CONNECTOR_ERROR","CONNECTOR_NOT_LIVE","CONNECTOR_DISABLED","NO_BUILD","MISSING_SITE") for x in acts),
            "actions_policy_blocked":sum(x["status"]=="BLOCKED_POLICY" for x in acts),
            "receipts_total":len(self.db.rows("SELECT * FROM receipts")),
            "execution_scores_total":len(self.db.rows("SELECT * FROM execution_scores")),
            "automatic_financial_execution":False,
            "automatic_wallet_signing":False,
            "automatic_fund_transfers":False,
            "automatic_domain_purchase":False,
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
