class QualityGovernor:
    """162: prevent weak autonomous outputs from advancing without rework."""
    def evaluate(self,item):
        tests=bool(item.get("tests_pass",False)); confidence=float(item.get("confidence",0))
        complete=float(item.get("completeness",0))
        pass_gate=tests and confidence>=.65 and complete>=.75
        return {"passed":pass_gate,"next_action":"advance" if pass_gate else "autonomous_rework"}
