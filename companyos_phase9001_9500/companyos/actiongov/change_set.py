class ChangeSetBuilder:
    def build(self, actions):
        return {
            "count":len(actions or []),
            "actions":list(actions or []),
            "atomic":all(bool(a.get("reversible",False)) for a in actions or [])
        }
