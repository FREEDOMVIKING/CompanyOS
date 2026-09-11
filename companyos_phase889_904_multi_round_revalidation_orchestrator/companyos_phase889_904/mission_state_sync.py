class MissionStateSync:
    """900: sync next round state back into mission context."""
    def apply(self,mission,round_no,history):
        m=dict(mission or {}); ctx=dict(m.get("context") or {})
        ctx["revalidation_round"]=int(round_no)
        ctx["revalidation_history"]=list(history or [])
        m["context"]=ctx
        m["attempts"]=max(int(m.get("attempts",0)),int(round_no))
        return m
