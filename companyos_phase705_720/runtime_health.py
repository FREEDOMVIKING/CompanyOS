class RuntimeHealth:
    """715: unified runtime sanity checks."""

    def evaluate(self, state, last_cycle=None):
        failures = int(state.get("consecutive_failures",0))
        cycle_ok = None if last_cycle is None else bool(last_cycle.get("success"))
        return {
            "healthy": failures < 3 and cycle_ok is not False,
            "consecutive_failures": failures,
            "last_cycle_success": cycle_ok,
            "safe_mode": bool(state.get("safe_mode",False)),
        }
