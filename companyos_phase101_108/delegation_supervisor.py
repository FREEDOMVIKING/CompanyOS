class DelegationSupervisor:
    """103: supervise specialist-agent assignments and completion quality."""
    def review(self, assignments):
        result=[]
        for a in assignments:
            quality=float(a.get("quality",0)); complete=bool(a.get("complete",False))
            result.append({**a,"accepted":complete and quality>=.7,
            "next_action":"accept" if complete and quality>=.7 else "revise_or_reassign"})
        return result
