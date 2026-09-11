from .opportunity_schema import OpportunitySchema
from .opportunity_scoring import OpportunityScoring
from .validation_plan import ValidationPlan

class OpportunityPipeline:
    def __init__(self):
        self.schema = OpportunitySchema()
        self.scoring = OpportunityScoring()
        self.validation = ValidationPlan()

    def rank(self, opportunities):
        ranked = []
        for raw in opportunities:
            normalized = self.schema.normalize(raw)
            if not normalized["valid"]:
                ranked.append({
                    "valid": False,
                    "missing": normalized["missing"],
                    "opportunity": raw,
                    "score": 0,
                })
                continue
            score = self.scoring.score(raw.get("metrics", {}))
            ranked.append({
                "valid": True,
                "opportunity": raw,
                "score": score,
                "validation_plan": self.validation.create(raw),
            })
        return sorted(ranked, key=lambda x: x.get("score", 0), reverse=True)
