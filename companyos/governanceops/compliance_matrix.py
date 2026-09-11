class ComplianceMatrix:
    def map(self, requirements, controls):
        rows=[]
        controls=set(controls or [])
        for r in requirements or []:
            required=set(r.get("required_controls",[]))
            covered=sorted(required & controls)
            missing=sorted(required-controls)
            rows.append({
                "requirement":r.get("requirement"),
                "covered_controls":covered,
                "missing_controls":missing,
                "compliant":not missing
            })
        return rows
