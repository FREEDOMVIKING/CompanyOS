class DecisionJournal:
    """174: create structured decision records for autonomous learning/audit."""
    def record(self, decision, rationale, expected, reversible=True):
        return {"decision":decision,"rationale":rationale,"expected_outcome":expected,
                "reversible":bool(reversible),"review_status":"pending_outcome"}
    def review(self, record, actual_score):
        expected=float(record.get("expected_outcome",0)); actual=float(actual_score)
        return {**record,"actual_outcome":actual,"prediction_error":round(actual-expected,4),"review_status":"reviewed"}
