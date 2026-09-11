class DependencyResolver:
    def order(self, items):
        items={i["id"]:dict(i) for i in items or []}
        ordered=[]
        remaining=set(items)
        while remaining:
            progress=False
            for iid in list(remaining):
                deps=set(items[iid].get("depends_on",[]))
                if deps.issubset({x["id"] for x in ordered}):
                    ordered.append(items[iid]); remaining.remove(iid); progress=True
            if not progress:
                ordered.extend(items[i] for i in sorted(remaining))
                break
        return ordered
