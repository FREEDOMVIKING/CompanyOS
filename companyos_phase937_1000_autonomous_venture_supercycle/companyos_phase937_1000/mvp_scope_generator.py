class MVPScopeGenerator:
    """965-968: derive MVP scope from proven validation evidence."""
    def generate(self, build_mission):
        ctx = dict((build_mission or {}).get("context") or {})
        validation = dict(ctx.get("validation_result") or {})
        scores = dict(validation.get("scores") or {})
        return {
            "goal": ctx.get("objective"),
            "must_have": [
                "solve validated core problem",
                "instrument usage and outcome metrics",
                "support safe rollback",
                "include minimal operator documentation",
            ],
            "success_metrics": {
                "problem_fit": scores.get("problem_evidence",0),
                "pricing_signal": scores.get("pricing_validation",0),
                "validation_confidence": scores.get("validation_confidence",0),
            },
            "non_goals": [
                "premature scale",
                "unvalidated feature expansion",
                "irreversible external commitments",
            ]
        }
