class EvidenceAcquisitionPlanner:
    def plan(self,gaps):
        out=[]
        for g in gaps:
            d=g["dimension"]
            q={"problem_evidence":"customer pain frequency severity current workarounds",
               "pricing_validation":"pricing willingness to pay budgets purchase intent",
               "validation_confidence":"customer demand proof pricing alternatives commercial intent",
               "contradictions":"conflicting claims primary sources verification"}.get(d,d)
            out.append({"dimension":d,"query":q,"minimum_new_evidence":2,"require_source_diversity":True})
        return out
