from typing import Any, Dict
class LearningSystem:
    """75: outcome learning that never silently rewrites safety policy."""
    def learn(self, expected:float, actual:float, context:Dict[str,Any]|None=None):
        delta=float(actual)-float(expected)
        return {"expected":float(expected),"actual":float(actual),"delta":round(delta,4),
        "lesson":"reinforce" if delta>0 else "revalidate" if delta<0 else "neutral",
        "context":context or {},"auto_policy_change":False}
