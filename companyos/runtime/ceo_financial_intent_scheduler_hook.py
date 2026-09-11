from __future__ import annotations
from typing import Any
from companyos.runtime.ceo_financial_intent_inbox import process_inbox

def run_ceo_financial_intent_hook(context: Any = None) -> dict[str, Any]:
    return process_inbox(max_items=5)
