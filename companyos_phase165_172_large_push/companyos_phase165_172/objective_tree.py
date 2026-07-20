class ObjectiveTree:
    """165: recursively decompose company objectives into executable outcomes."""
    def build(self, objective, depth=2):
        root={"objective":objective,"level":0,"autonomous":True,"children":[]}
        frontier=[root]
        for level in range(1,max(1,int(depth))+1):
            nxt=[]
            for node in frontier:
                for suffix in ("validate","build","measure"):
                    child={"objective":f"{suffix}:{node['objective']}","level":level,"autonomous":True,"children":[]}
                    node["children"].append(child); nxt.append(child)
            frontier=nxt
        return root
