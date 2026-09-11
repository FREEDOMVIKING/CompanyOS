import json
from pathlib import Path
from datetime import datetime, timezone

class SignerValidationReport:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"signer_validation_report.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, signer_probe, unsigned_intent, signature_check, simulation):
        checks = {
            "signer_probe_success": bool((signer_probe or {}).get("success")),
            "unsigned_intent_built": bool((unsigned_intent or {}).get("success")),
            "signature_structure_valid": bool((signature_check or {}).get("passed")),
            "simulation_passed": bool((simulation or {}).get("passed")),
            "broadcast_attempted": bool((simulation or {}).get("broadcast_attempted")),
        }

        ready_for_live_review = all([
            checks["signer_probe_success"],
            checks["unsigned_intent_built"],
            checks["signature_structure_valid"],
            checks["simulation_passed"],
            not checks["broadcast_attempted"],
        ])

        report = {
            "success": True,
            "status":"signer_validation_report_complete",
            "checks":checks,
            "ready_for_live_review":ready_for_live_review,
            "ready_for_live":False,
            "manual_enable_still_required":True,
            "timestamp":datetime.now(timezone.utc).isoformat(),
        }
        self.path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
