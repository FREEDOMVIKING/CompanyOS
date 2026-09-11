from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from companyos.solanasim.rpc import SolanaRpcClient


class PendingTransactionRecovery:
    TERMINAL = {"confirmed", "finalized", "failed"}

    def __init__(self, root=None, rpc=None):
        self.root = Path(root or Path.home() / "companyos")
        self.runtime = self.root / "companyos_runtime"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.pending_path = self.runtime / "pending_transactions.json"
        self.history_path = self.runtime / "transaction_confirmation_history.jsonl"
        self.rpc = rpc or SolanaRpcClient()

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _load(self):
        if not self.pending_path.exists():
            return {}
        try:
            data = json.loads(self.pending_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save(self, data):
        tmp = self.pending_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.pending_path)

    def _history(self, row):
        record = dict(row or {})
        record.setdefault("timestamp", self._now())
        with self.history_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")

    def register(self, tx_id, *, destination=None, amount=None, source=None,
                 execution_status=None, receipt_id=None, metadata=None):
        if not tx_id:
            return {"success": False, "status": "missing_tx_id"}

        data = self._load()
        existing = data.get(tx_id)
        row = dict(existing or {})
        row.update({
            "tx_id": tx_id,
            "state": row.get("state") or "pending",
            "destination": destination if destination is not None else row.get("destination"),
            "amount": amount if amount is not None else row.get("amount"),
            "source": source if source is not None else row.get("source"),
            "execution_status": execution_status or row.get("execution_status"),
            "receipt_id": receipt_id or row.get("receipt_id"),
            "metadata": metadata if metadata is not None else row.get("metadata"),
            "updated_at": self._now(),
        })
        row.setdefault("created_at", self._now())
        row.setdefault("check_count", 0)
        data[tx_id] = row
        self._save(data)

        return {
            "success": True,
            "status": "pending_registered" if existing is None else "pending_already_registered",
            "tx_id": tx_id,
            "rebroadcast_performed": False,
        }

    def status(self, tx_id):
        return self._load().get(tx_id)

    def pending(self):
        return list(self._load().values())

    def _classify(self, tx_id):
        rpc_result = self.rpc.signature_status(tx_id)

        if not rpc_result.get("success"):
            return {
                "state": "pending",
                "passed": False,
                "rpc_checked": True,
                "confirmation_error": rpc_result,
            }

        values = (rpc_result.get("result") or {}).get("value") or []
        sig = values[0] if values else None

        if not sig:
            return {
                "state": "pending",
                "passed": False,
                "rpc_checked": True,
                "confirmation_error": "signature_not_found",
            }

        err = sig.get("err")
        confirmation = sig.get("confirmationStatus")

        if err is not None:
            state = "failed"
            passed = False
        elif confirmation in {"confirmed", "finalized"}:
            state = confirmation
            passed = True
        else:
            state = "pending"
            passed = False

        return {
            "state": state,
            "passed": passed,
            "rpc_checked": True,
            "confirmation_status": confirmation,
            "confirmation_error": err,
        }

    def reconcile_one(self, tx_id):
        data = self._load()
        row = data.get(tx_id)
        if row is None:
            return {"success": False, "status": "pending_tx_not_found", "tx_id": tx_id}

        result = self._classify(tx_id)
        row["check_count"] = int(row.get("check_count", 0)) + 1
        row["updated_at"] = self._now()
        row["state"] = result["state"]
        row["last_verification"] = result

        if result["state"] in self.TERMINAL:
            data.pop(tx_id, None)
            self._save(data)
            history = dict(row)
            history["terminal_state"] = result["state"]
            self._history(history)
            return {
                "success": True,
                "status": "pending_reconciled_terminal",
                "tx_id": tx_id,
                "state": result["state"],
                "verification": result,
                "rebroadcast_performed": False,
            }

        data[tx_id] = row
        self._save(data)
        return {
            "success": True,
            "status": "pending_still_waiting",
            "tx_id": tx_id,
            "state": "pending",
            "verification": result,
            "rebroadcast_performed": False,
        }

    def reconcile_all(self, limit=100):
        txids = list(self._load().keys())[:max(0, int(limit))]
        results = [self.reconcile_one(txid) for txid in txids]
        return {
            "success": True,
            "status": "pending_reconciliation_complete",
            "checked": len(results),
            "results": results,
            "rebroadcast_performed": False,
        }
