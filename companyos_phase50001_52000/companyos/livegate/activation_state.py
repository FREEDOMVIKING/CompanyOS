import json
from pathlib import Path

class ActivationState:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"live_activation_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, readiness):
        state = {
            "controlled_live_review_ready": bool(readiness.get("ready_for_controlled_live_review")),
            "autonomous_live_enabled": False,
            "requires_one_shot_authorization": True,
            "requires_treasury_policy": True,
            "requires_kill_switch_clear": True,
            "requires_receipt_verification": True,
        }
        self.path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state
