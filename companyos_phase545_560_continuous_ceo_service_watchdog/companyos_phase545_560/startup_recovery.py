class StartupRecovery:
    """557: normalize service state after unclean shutdown."""

    def recover(self, state):
        state = dict(state or {})
        if state.get("running"):
            state["running"] = False
            state["recovered_from_unclean_shutdown"] = True
        else:
            state.setdefault("recovered_from_unclean_shutdown", False)
        return state
