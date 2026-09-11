class TreasuryReconciler:
    def reconcile(self, ledger_rows, provider_transactions):
        ledger_ids = {str(r.get("tx_id")) for r in ledger_rows if r.get("tx_id")}
        provider_ids = {str(r.get("tx_id")) for r in provider_transactions if r.get("tx_id")}
        return {
            "matched": sorted(ledger_ids & provider_ids),
            "missing_in_provider": sorted(ledger_ids - provider_ids),
            "missing_in_ledger": sorted(provider_ids - ledger_ids),
            "balanced": ledger_ids == provider_ids
        }
