import json
from pathlib import Path

class LiveReadinessGate:
    def __init__(self, root):
        self.root = Path(root)

    def _read_json(self, *paths):
        for p in paths:
            p = Path(p)
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return None

    def evaluate(self):
        identity = self._read_json(
            Path.home()/"companyos_runtime"/"wallet_identity.json",
            self.root/".companyos_runtime"/"wallet_identity.json",
        ) or {}
        signer = self._read_json(
            self.root/".companyos_runtime"/"signer_validation_report.json"
        ) or {}
        compat = self._read_json(
            self.root/".companyos_runtime"/"signer_compatibility_report.json"
        ) or {}
        activation = self._read_json(
            self.root/".companyos_runtime"/"wallet_activation_readiness.json"
        ) or {}

        checks = {
            "wallet_identity_present": bool(identity.get("public_address")),
            "private_key_exposed_false": identity.get("private_key_exposed") is False,
            "signer_validation_report_present": bool(signer),
            "signer_compatibility_report_present": bool(compat),
            "binding_preflight_ready": bool(activation.get("ready_for_dry_run")),
        }

        hard_ready = all([
            checks["wallet_identity_present"],
            checks["private_key_exposed_false"],
            checks["binding_preflight_ready"],
        ])

        return {
            "success": True,
            "status": "live_readiness_evaluated",
            "checks": checks,
            "ready_for_controlled_live_review": hard_ready,
            "autonomous_live_enabled": False,
            "reason": "controlled_review_ready" if hard_ready else "prerequisites_incomplete",
        }
