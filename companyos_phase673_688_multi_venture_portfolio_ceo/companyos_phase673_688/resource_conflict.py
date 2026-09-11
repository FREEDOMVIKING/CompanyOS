class ResourceConflict:
    """683: detect specialist capacity conflicts."""

    def detect(self, venture_demands, capacity):
        conflicts=[]
        for role, limit in capacity.items():
            demand=sum(int(v.get("roles",{}).get(role,0)) for v in venture_demands)
            if demand > int(limit):
                conflicts.append({"role":role,"demand":demand,"capacity":int(limit)})
        return {"has_conflict":bool(conflicts),"conflicts":conflicts}
