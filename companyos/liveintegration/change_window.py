class ChangeWindow:
    def evaluate(self, change, current_load=.5):
        risk=float(change.get("risk",0))
        reversible=bool(change.get("reversible",False))
        allowed=current_load<.8 and risk<.6 and reversible
        return {
            "allowed":allowed,
            "reason":"safe_change_window" if allowed else "defer_or_require_approval"
        }
