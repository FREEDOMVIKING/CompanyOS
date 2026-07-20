from __future__ import annotations

from typing import Any, Dict


class RepairAgent:
    """216: request targeted repairs from the configured model adapter."""

    def repair(self, adapter, workspace, build_spec, verification):
        prompt = {
            "task": "Repair the generated capability so all required tests pass.",
            "build_spec": build_spec,
            "verification_failure": verification,
            "workspace": str(workspace),
            "instructions": [
                "return only changed files in JSON",
                "preserve existing behavior unless required",
                "keep the patch reversible",
            ],
        }
        return adapter.generate(prompt)
