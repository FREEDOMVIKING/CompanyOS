from companyos.paymentops.connector_base import PaymentConnector

class CryptoPaymentConnector(PaymentConnector):
    name = "existing_companyos_crypto_wallet"

    def __init__(self, wallet_adapter):
        self.wallet = wallet_adapter

    def health(self):
        address = self.wallet.get_address()
        balance = self.wallet.get_balance()
        return {
            "success": bool(address.get("success") and balance.get("success")),
            "connector": self.name,
            "address_ready": bool(address.get("success")),
            "balance_ready": bool(balance.get("success")),
        }

    def get_balance(self):
        return self.wallet.get_balance()

    def execute_transfer(self, *, amount, destination, memo="", idempotency_key=None):
        return self.wallet.execute_transfer(
            amount=amount,
            destination=destination,
            memo=memo,
            idempotency_key=idempotency_key
        )

    def list_transactions(self, limit=100):
        return self.wallet.list_transactions(limit=limit)
