class BuildDispatch:
    """894: normalize build mission dispatch."""
    def dispatch(self,mission):
        return {"dispatched":bool(mission),"destination":"build_queue","mission":mission}
