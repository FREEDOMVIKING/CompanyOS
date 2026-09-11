class BalanceAndFeeGuard:
    def validate(self, balance, amount, estimated_fee, min_reserve):
        balance = float(balance)
        amount = float(amount)
        estimated_fee = float(estimated_fee)
        min_reserve = float(min_reserve)
        remaining = balance - amount - estimated_fee
        if remaining < min_reserve:
            return {
                "allowed":False,
                "status":"reserve_floor_violation",
                "remaining_after":remaining,
                "min_reserve":min_reserve
            }
        return {
            "allowed":True,
            "status":"balance_and_fee_check_passed",
            "remaining_after":remaining
        }
