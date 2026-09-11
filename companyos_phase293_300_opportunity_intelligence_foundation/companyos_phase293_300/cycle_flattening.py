class CycleFlatteningPolicy:
    def supervisor_limits_for_rounds(self, rounds: int):
        rounds = max(1, int(rounds))
        return {
            "outer_rounds": rounds,
            "supervisor_cycles_per_round": 1,
            "total_expected_cycles": rounds,
        }
