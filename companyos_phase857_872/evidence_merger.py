class EvidenceMerger:
    def merge(self,old,new):
        seen=set(); merged=[]
        for e in list(old or [])+list(new or []):
            key=e.get("id") or (e.get("url"),e.get("title"))
            if key in seen: continue
            seen.add(key); merged.append(e)
        return merged
