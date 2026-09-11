class PortfolioSynergyEngine:
    def evaluate(self, ventures):
        synergies=[]
        for i,a in enumerate(ventures or []):
            for b in (ventures or [])[i+1:]:
                shared=set(a.get("capabilities",[])) & set(b.get("capabilities",[]))
                customer_overlap=set(a.get("customer_segments",[])) & set(b.get("customer_segments",[]))
                if shared or customer_overlap:
                    synergies.append({
                        "venture_a":a.get("venture_id"),
                        "venture_b":b.get("venture_id"),
                        "shared_capabilities":sorted(shared),
                        "customer_overlap":sorted(customer_overlap),
                        "synergy_score":len(shared)+len(customer_overlap)
                    })
        return sorted(synergies,key=lambda x:x["synergy_score"],reverse=True)
