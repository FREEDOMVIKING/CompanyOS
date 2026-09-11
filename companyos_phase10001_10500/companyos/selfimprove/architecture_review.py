class ArchitectureReview:
    def evaluate(self, modules):
        duplicates={}
        seen={}
        for m in modules or []:
            role=m.get("role")
            if role in seen:
                duplicates.setdefault(role,[]).extend([seen[role],m.get("name")])
            else:
                seen[role]=m.get("name")
        return {
            "duplicate_roles":duplicates,
            "simplification_needed":bool(duplicates)
        }
