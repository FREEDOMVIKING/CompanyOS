class ProductValidationEngine:
    def evaluate(self, experiments):
        passed=[]
        failed=[]
        for e in experiments or []:
            result=float(e.get("result",0))
            threshold=float(e.get("success_threshold",0))
            (passed if result>=threshold else failed).append(e.get("name"))
        return {
            "validated":bool(passed) and not failed,
            "passed":passed,
            "failed":failed,
            "recommendation":"advance" if bool(passed) and not failed else "iterate"
        }
