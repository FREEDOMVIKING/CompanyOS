class StressPlan:
    """732: bounded multi-cycle stress plan."""

    def build(self, rounds=3):
        rounds=max(1,min(int(rounds),10))
        return {
            "rounds":rounds,
            "missions_per_round":1,
            "safe_bounded":True,
            "external_actions":False,
            "financial_actions":False,
        }
