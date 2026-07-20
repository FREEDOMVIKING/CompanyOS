from __future__ import annotations

class ModelMissionRunner:
    """232: run one genuine model-backed self-build mission through Phase 228."""

    def __init__(self, real_coder_loop):
        self.loop = real_coder_loop

    def run_one(self, goals, capabilities, max_attempts=3):
        inspection = self.loop.inspect(goals, capabilities)
        if not inspection.get("coder_configured"):
            return {
                "success": False,
                "stage": "configuration",
                "reason": "external_coder_not_configured",
                "inspection": inspection,
            }
        return self.loop.build_selected_gap(goals, capabilities, max_attempts=max_attempts)
