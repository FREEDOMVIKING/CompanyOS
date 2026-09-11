import uuid
from .connector_base import PaymentConnector

class SandboxPaymentConnector(PaymentConnector):
    name = "sandbox"

    def __init__(self, starting_balance=1000.0):
        self.balance = float(starting_balance)
        self.transactions = []

    def get_balance(self):
        return {"success":True, "balance":self.balance, "currency":"USD"}

    def execute_transfer(self, *, amount, destination, memo="", idempotency_key=None):
        amount = float(amount)
        if amount <= 0:
            return {"success":False,"error":"invalid_amount"}
        if amount > self.balance:
            return {"success":False,"error":"insufficient_funds"}

        tx_id = "sandbox_" + uuid.uuid4().hex[:16]
        self.balance -= amount
        row = {
            "success":True,
            "tx_id":tx_id,
            "amount":amount,
            "destination":destination,
            "memo":memo,
            "idempotency_key":idempotency_key,
            "status":"settled",
            "currency":"USD"
        }
        self.transactions.append(row)
        return row

    def list_transactions(self, limit=100):
        return list(self.transactions[-int(limit):])
