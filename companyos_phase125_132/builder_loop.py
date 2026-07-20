from __future__ import annotations
from typing import Any, Dict, List

class BuilderLoop:
    """127: autonomous build-test-revise loop for internal products/code."""

    def next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        tests_pass = bool(state.get("tests_pass", False))
        build_exists = bool(state.get("build_exists", False))
        validated = bool(state.get("validated", False))

        if not build_exists:
            return {"action": "build_mvp", "autonomous": True}
        if not tests_pass:
            return {"action": "debug_and_retest", "autonomous": True}
        if not validated:
            return {"action": "run_validation_experiment", "autonomous": True}
        return {"action": "prepare_next_iteration", "autonomous": True}
