class CycleProbe:
    """723: inspect unified runtime cycle result."""

    def inspect(self, result):
        return {
            "status":result.get("status"),
            "success":bool(result.get("success")),
            "executed":int(result.get("executed",0)),
            "remaining":int(result.get("remaining",0)),
            "has_cycle":bool(result.get("cycle")),
        }
