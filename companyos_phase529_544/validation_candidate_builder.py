class ValidationCandidateBuilder:
    """532: convert high-quality candidates into validation-ready theses."""

    def build(self, candidate):
        return {
            "name":candidate.get("name"),
            "customer":"target customer segment inferred during validation",
            "core_problem":f"Repeated evidence around {candidate.get('theme','business problem').replace('_',' ')}",
            "business_model":{"primary":"subscription/service model to validate"},
            "quality_score":candidate.get("quality_score"),
            "evidence_links":candidate.get("evidence_links",[])[:15],
            "source_count":candidate.get("source_count",0),
            "dimensions":candidate.get("dimensions",{}),
        }
