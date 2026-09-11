import json
from pathlib import Path

class WalletActivationReadiness:
    def __init__(self, root):
        self.root = Path(root)
        self.binding = self.root / ".companyos_runtime" / "crypto_wallet_binding.json"

    def evaluate(self, preflight):
        binding_ok = self.binding.exists()
        preflight_ok = bool((preflight or {}).get("passed"))

        state = {
            "binding_present": binding_ok,
            "preflight_passed": preflight_ok,
            "ready_for_dry_run": bool(binding_ok and preflight_ok),
            "ready_for_live": False,
            "live_enable_requires_explicit_manual_step": True,
            "reason": (
                "binding_and_preflight_ready"
                if binding_ok and preflight_ok
                else "binding_or_preflight_incomplete"
            )
        }

        out = self.root / ".companyos_runtime" / "wallet_activation_readiness.json"
        out.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state
