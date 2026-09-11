class RegressionMatrix:
    def evaluate(self, checks):
        rows=[]
        for c in checks or []:
            passed=bool(c.get("passed",False))
            rows.append({**c,"status":"pass" if passed else "fail"})
        return {"passed":all(r["status"]=="pass" for r in rows) if rows else True,
                "failures":[r for r in rows if r["status"]=="fail"],"checks":rows}
