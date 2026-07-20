from __future__ import annotations
from typing import Any, Dict

class OutputDiagnostics:
    """272: compact model-output diagnostics for autonomous retry decisions."""

    def summarize(self, raw: Any, extraction_count: int, recovery: Dict[str, Any], contract: Dict[str, Any]):
        raw_text = str(raw)
        return {
            "raw_type": type(raw).__name__,
            "raw_length": len(raw_text),
            "extracted_candidates": extraction_count,
            "json_recovery_success": bool(recovery.get("success")),
            "json_recovery_method": recovery.get("method"),
            "contract_success": bool(contract.get("success")),
            "contract_reason": contract.get("reason"),
        }
