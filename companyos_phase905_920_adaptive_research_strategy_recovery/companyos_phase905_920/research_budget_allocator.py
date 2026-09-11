class ResearchBudgetAllocator:
    """912: allocate bounded attempts toward the weakest validation dimensions."""
    def allocate(self, causes, max_attempts=4):
        reasons=list((causes or {}).get("reasons",[]))
        if not reasons:return {"general":max_attempts}
        per=max(1,int(max_attempts)//len(reasons))
        out={r:per for r in reasons}
        remaining=int(max_attempts)-sum(out.values())
        if remaining>0: out[reasons[0]]+=remaining
        return out
