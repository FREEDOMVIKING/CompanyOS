class DependencyAuditor:
    def inspect(self, dependencies):
        duplicates=[]
        seen=set()
        for d in dependencies or []:
            name=d.get("name")
            if name in seen: duplicates.append(name)
            seen.add(name)
        return {"valid":not duplicates,"duplicates":duplicates,"count":len(dependencies or [])}
