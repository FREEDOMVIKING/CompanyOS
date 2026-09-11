class SLOEngine:
    def evaluate(self, metrics, targets):
        out={}
        for key,target in (targets or {}).items():
            actual=float((metrics or {}).get(key,0))
            direction="min" if key in ("availability","success_rate") else "max"
            met=actual>=float(target) if direction=="min" else actual<=float(target)
            out[key]={"actual":actual,"target":float(target),"met":met}
        return {"slos":out,"all_met":all(x["met"] for x in out.values()) if out else True}
