class ReceiptReconciler:
    def reconcile(self, broadcast_result, confirmation_result=None):
        b = broadcast_result or {}
        c = confirmation_result or {}
        txid = b.get("tx_id") or b.get("signature") or b.get("transaction_hash") or b.get("hash")
        confirmed = bool(
            c.get("confirmed")
            or c.get("success")
            or c.get("status") in {"confirmed","finalized","settled"}
            or b.get("status") in {"confirmed","finalized","settled"}
        )
        return {
            "success": bool(txid and confirmed),
            "tx_id": txid,
            "confirmed": confirmed,
            "status": "receipt_reconciled" if txid and confirmed else "receipt_unverified"
        }
