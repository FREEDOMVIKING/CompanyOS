class PaymentConnector:
    name = "base"

    def health(self):
        return {"success": True, "connector": self.name}

    def get_balance(self):
        raise NotImplementedError

    def execute_transfer(self, *, amount, destination, memo="", idempotency_key=None):
        raise NotImplementedError

    def list_transactions(self, limit=100):
        return []
