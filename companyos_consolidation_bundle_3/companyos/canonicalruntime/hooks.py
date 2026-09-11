from __future__ import annotations
from typing import Any, Dict
from .bridge import UnifiedCEOCanonicalBridge

_bridge = None

def get_bridge() -> UnifiedCEOCanonicalBridge:
    global _bridge
    if _bridge is None:
        _bridge = UnifiedCEOCanonicalBridge()
    return _bridge

def submit_ceo_goal(objective: str, context: Dict[str, Any] | None = None, **kwargs):
    return get_bridge().submit_ceo_goal(objective, context, **kwargs)

def submit_opportunity(title: str, **kwargs):
    return get_bridge().submit_opportunity(title, **kwargs)

def submit_research_result(research_question: str, **kwargs):
    return get_bridge().submit_research_result(research_question, **kwargs)
