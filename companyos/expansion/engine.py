from pathlib import Path
from datetime import datetime, timezone
import os, json

from .storage import read_json, write_json, append_json
from .capabilities import capability_manifest
from .approvals import ApprovalGate
from .connectors import ConnectorRegistry, ProposalConnector
from . import services

class ExpansionEngine:
    def __init__(self, home=None):
        self.home = Path(home or os.environ.get("COMPANYOS_HOME", str(Path.home() / "companyos")))
        self.runtime = self.home / "companyos_runtime" / "expansion21"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.approvals = ApprovalGate(self.runtime)
        self.connectors = ConnectorRegistry()
        for name in ["web_search","email","domains","banking","crypto","hosting","crm","accounting"]:
            self.connectors.register(name, ProposalConnector())

    def run_cycle(self):
        manifest = capability_manifest()
        status = {
            "phase": "19501-21000",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "capability_count": len(manifest),
            "capabilities": manifest,
            "connectors": self.connectors.status(),
            "queued_actions": len(read_json(self.runtime / "actions.json", [])),
            "approved_actions": len(read_json(self.runtime / "approvals.json", [])),
            "safety": {
                "default_external_mode": "proposal_only",
                "financial_actions": "approval_required",
                "legal_actions": "human_review_required",
                "production_deployments": "approval_required",
            },
        }
        write_json(self.runtime / "latest_expansion_status.json", status)
        return status

    def propose(self, capability, action, payload, risk_level="medium"):
        gate = self.approvals.evaluate(action, risk_level)
        action_id = f"{capability}:{action}:{int(datetime.now(timezone.utc).timestamp()*1000)}"
        record = {
            "action_id": action_id,
            "capability": capability,
            "action": action,
            "payload": payload,
            "risk_level": risk_level,
            **gate,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        append_json(self.runtime / "actions.json", record)
        append_json(self.runtime / "audit_log.json", {"type":"action_proposed", **record})
        return record

    def execute_internal_demo(self):
        opportunity = services.OpportunityDiscovery().plan(["AI services for local businesses"])[0]
        product = services.ProductFactory().create_blueprint(opportunity["topic"])
        site = services.WebsiteBuilder().build_spec({"name":"Local AI Services"})
        campaign = services.MarketingEngine().campaign(product["product_id"], "local businesses")
        company = services.Portfolio().company_record("Local AI Services", "Automate repetitive work")
        result = {
            "opportunity": opportunity,
            "product": product,
            "website": site,
            "campaign": campaign,
            "company": company,
        }
        write_json(self.runtime / "internal_demo.json", result)
        return result
