from datetime import datetime, timezone
from pathlib import Path
from .storage import read_json, write_json

IRREVERSIBLE = {
    "send_email", "purchase_domain", "transfer_funds", "sign_transaction",
    "deploy_production", "publish_website", "submit_legal_filing", "hire_candidate",
    "terminate_vendor", "execute_external_api"
}

class ApprovalGate:
    def __init__(self, runtime_dir: Path):
        self.path = Path(runtime_dir) / "approvals.json"

    def evaluate(self, action: str, risk_level: str = "medium"):
        approval_required = action in IRREVERSIBLE or risk_level in {"high", "critical"}
        return {
            "approval_required": approval_required,
            "execution_mode": "proposal_only" if approval_required else "internal_auto",
        }

    def approve(self, action_id: str, approved_by: str = "owner"):
        rows = read_json(self.path, [])
        rows.append({
            "action_id": action_id,
            "approved": True,
            "approved_by": approved_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        write_json(self.path, rows)
        return rows[-1]

    def is_approved(self, action_id: str) -> bool:
        return any(x.get("action_id") == action_id and x.get("approved") for x in read_json(self.path, []))
