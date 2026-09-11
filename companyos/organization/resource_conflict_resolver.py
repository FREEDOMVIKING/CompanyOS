class ResourceConflictResolver:
    def resolve(self, claims):
        by_resource={}
        for c in claims or []:
            by_resource.setdefault(c.get("resource"),[]).append(c)
        resolutions=[]
        for resource, rows in by_resource.items():
            winner=max(rows,key=lambda x:float(x.get("priority",0)))
            resolutions.append({"resource":resource,"winner":winner.get("department"),
                                "losers":[x.get("department") for x in rows if x is not winner]})
        return resolutions
