class OpportunityPipeline:
    """182: autonomously move opportunities through discovery and validation."""
    def advance(self,opportunities):
        out=[]
        for o in opportunities:
            evidence=float(o.get("evidence",0));demand=float(o.get("demand",0))
            if evidence<.3: stage="research"
            elif demand<.5: stage="validate_demand"
            elif evidence<.7: stage="prototype"
            else: stage="incubate"
            out.append({**o,"next_stage":stage,"autonomous":True})
        return out
