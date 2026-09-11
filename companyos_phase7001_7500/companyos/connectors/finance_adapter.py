class FinanceAdapter:
    def read_action(self, account_ref):
        return {"capability":"finance_read","kind":"read_financial_status","account_ref":account_ref}

    def transfer_action(self, from_ref, to_ref, amount):
        return {
            "capability":"finance_write",
            "kind":"bank_transfer",
            "from_ref":from_ref,
            "to_ref":to_ref,
            "amount":float(amount)
        }
