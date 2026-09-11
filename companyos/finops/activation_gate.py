import json
import os
from pathlib import Path
from datetime import datetime, timezone

class LiveActivationGate:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "financial_activation_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def evaluate(self, readiness, validation_report):
        required = {
            "adapter_present": bool(readiness.get("adapter_present")),
            "signer_command_configured": bool(readiness.get("signer_command_configured")),
            "at_least_one_rpc": any([
                readiness.get("solana_rpc_configured"),
                readiness.get("evm_rpc_configured"),
                readiness.get("bitcoin_rpc_configured"),
            ]),
            "validation_passed": bool(validation_report.get("passed")),
        }
        eligible = all(required.values())
        state = {
            "eligible_for_manual_live_enable": eligible,
            "requirements": required,
            "live_execution_currently_enabled": os.getenv(
                "COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION",""
            ).strip().lower() in {"1","true","yes","on"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Eligibility does not itself enable live execution."
        }
        self.path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state
