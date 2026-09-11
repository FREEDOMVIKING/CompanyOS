class TransactionPolicy:
    def __init__(self, max_single_amount=0.01, min_reserve=0.01):
        self.max_single_amount = float(max_single_amount)
        self.min_reserve = float(min_reserve)

    def validate(self, amount, destination, allowlist=None):
        amount = float(amount)
        allowlist = set(allowlist or [])
        if amount <= 0:
            return {"allowed":False,"status":"invalid_amount"}
        if amount > self.max_single_amount:
            return {"allowed":False,"status":"single_amount_limit_exceeded","limit":self.max_single_amount}
        if allowlist and destination not in allowlist:
            return {"allowed":False,"status":"destination_not_allowlisted"}
        return {"allowed":True,"status":"transaction_policy_passed"}
