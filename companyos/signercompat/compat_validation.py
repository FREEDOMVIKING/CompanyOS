import json
from pathlib import Path
from datetime import datetime, timezone

class SignerCompatibilityValidation:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"signer_compatibility_report.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, detector, bridge_result):
        compatible = bool((bridge_result or {}).get("success"))
        report = {
            "success": True,
            "status": "signer_compatibility_validation_complete",
            "signer_command_configured": bool((detector or {}).get("signer_command_configured")),
            "compatible_contract_confirmed": compatible,
            "broadcast_attempted": False,
            "ready_for_signer_validation_retry": compatible,
            "ready_for_live": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detector": detector,
            "bridge_result": bridge_result,
        }
        self.path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
