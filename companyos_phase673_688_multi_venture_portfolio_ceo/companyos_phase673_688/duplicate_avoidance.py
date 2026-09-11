import re

class DuplicateAvoidance:
    """675: flag near-duplicate venture concepts."""

    def _tokens(self, text):
        return {x for x in re.findall(r"[a-z0-9]+", str(text).lower()) if len(x) >= 4}

    def similarity(self, a, b):
        ta = self._tokens(f"{a.get('name','')} {a.get('problem','')} {a.get('theme','')}")
        tb = self._tokens(f"{b.get('name','')} {b.get('problem','')} {b.get('theme','')}")
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / max(1, len(ta | tb))

    def check(self, candidate, existing, threshold=0.65):
        matches = []
        for v in existing:
            sim = self.similarity(candidate, v)
            if sim >= threshold:
                matches.append({"venture_id":v.get("venture_id"),"similarity":round(sim,3)})
        return {"duplicate_risk":bool(matches),"matches":matches}
