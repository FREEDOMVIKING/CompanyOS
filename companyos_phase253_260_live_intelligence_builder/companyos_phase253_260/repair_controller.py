from __future__ import annotations

class RepairController:
    """257: feed exact compile/test failure evidence back to the coding model."""

    def make_prompt(self, original_payload, verification, attempt):
        return {
            **original_payload,
            "repair_mode": True,
            "repair_attempt": int(attempt),
            "failure_evidence": verification,
            "repair_instructions": [
                "Diagnose the exact failure from stdout/stderr.",
                "Return only complete changed files in the files JSON contract.",
                "Do not weaken or delete tests merely to force a pass.",
                "Preserve unrelated working behavior.",
                "Fix the smallest root cause and add regression coverage if needed.",
            ],
        }
