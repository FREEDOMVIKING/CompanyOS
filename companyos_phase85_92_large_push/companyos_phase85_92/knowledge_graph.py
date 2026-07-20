class KnowledgeGraph:
    """85: lightweight relationship graph for business knowledge."""
    def __init__(self): self.nodes={}; self.edges=[]
    def add(self,key,data=None): self.nodes[str(key)]=dict(data or {}); return self.nodes[str(key)]
    def link(self,a,relation,b):
        edge={"from":str(a),"relation":str(relation),"to":str(b)}
        if edge not in self.edges:self.edges.append(edge)
        return edge
    def neighbors(self,key):
        key=str(key)
        return [e for e in self.edges if e["from"]==key or e["to"]==key]
