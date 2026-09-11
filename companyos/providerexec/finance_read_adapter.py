class FinanceReadAdapter:
    name="finance_read_provider"
    capabilities=["finance_read"]
    live_supported=False

    def execute(self, request, timeout=30, live=False):
        return {
            "success":True,
            "simulated":not live,
            "adapter":self.name,
            "account_ref":request.get("account_ref"),
            "balances":request.get("seed_balances",{})
        }
