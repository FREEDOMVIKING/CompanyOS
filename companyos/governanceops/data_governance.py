class DataGovernanceEngine:
    def classify(self, assets):
        rows=[]
        for a in assets or []:
            sensitivity=a.get("sensitivity","internal")
            controls=["access_control","audit_logging"]
            if sensitivity in {"confidential","restricted"}:
                controls += ["encryption_at_rest","encryption_in_transit","least_privilege"]
            rows.append({**a,"required_controls":controls})
        return rows
