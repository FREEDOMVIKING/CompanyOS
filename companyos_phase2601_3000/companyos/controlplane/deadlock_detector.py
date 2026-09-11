class DeadlockDetector:
    def detect(self, waits):
        graph={}
        for w in waits or []:
            graph.setdefault(w.get("waiter"),set()).add(w.get("holder"))
        cycles=[]
        for start in graph:
            stack=[(start,[start])]
            while stack:
                node,path=stack.pop()
                for nxt in graph.get(node,set()):
                    if nxt==start and len(path)>1:
                        cyc=path+[start]
                        if cyc not in cycles:cycles.append(cyc)
                    elif nxt not in path:
                        stack.append((nxt,path+[nxt]))
        return {"deadlocked":bool(cycles),"cycles":cycles}
