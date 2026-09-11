class AccessReviewEngine:
    def review(self, identities):
        findings=[]
        for i in identities or []:
            if i.get("inactive") and i.get("permissions"):
                findings.append({"identity":i.get("identity"),"finding":"inactive_with_access"})
            if i.get("admin") and not i.get("mfa"):
                findings.append({"identity":i.get("identity"),"finding":"admin_without_mfa"})
        return {"findings":findings,"passed":not findings}
