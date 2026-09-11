class CrossVentureSalesEngine:
    def match(self, customers, ventures):
        matches=[]
        for c in customers or []:
            needs=set(c.get("needs",[]))
            for v in ventures or []:
                capabilities=set(v.get("capabilities",[]))
                overlap=len(needs & capabilities)
                if overlap:
                    matches.append({
                        "customer_id":c.get("customer_id"),
                        "venture_id":v.get("venture_id"),
                        "match_score":overlap
                    })
        return sorted(matches,key=lambda x:x["match_score"],reverse=True)
