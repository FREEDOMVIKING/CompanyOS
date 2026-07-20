from __future__ import annotations
from typing import Any, Dict, List

class BusinessBuilder:
    """135: generate an autonomous internal build plan for a venture."""

    def plan(self, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        name = blueprint.get("name", "venture")
        return [
            {"id": f"{name}:research", "task": "validate_customer_problem", "autonomous": True},
            {"id": f"{name}:offer", "task": "define_offer_and_pricing", "autonomous": True},
            {"id": f"{name}:build", "task": "build_mvp", "autonomous": True},
            {"id": f"{name}:test", "task": "run_internal_tests", "autonomous": True},
            {"id": f"{name}:measure", "task": "measure_results", "autonomous": True},
            {"id": f"{name}:iterate", "task": "iterate_from_evidence", "autonomous": True},
        ]
