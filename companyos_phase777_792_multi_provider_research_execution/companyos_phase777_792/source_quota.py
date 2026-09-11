class SourceQuota:
    """785: limit over-collection from a single provider."""
    def apply(self, evidence, max_per_provider=5):
        counts={}; kept=[]; dropped=[]
        for item in evidence or []:
            p=item.get("provider") or item.get("source_class","unknown")
            counts[p]=counts.get(p,0)+1
            if counts[p] <= max_per_provider:
                kept.append(item)
            else:
                dropped.append(item)
        return {"kept":kept,"dropped":dropped,"counts":counts}
