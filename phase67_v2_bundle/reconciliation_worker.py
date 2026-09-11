from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from companyos.walletintegration.pending_recovery import PendingTransactionRecovery


class PendingReconciliationWorker:
    """
    Phase 67 V2 worker.

    Safety:
    - read-only RPC confirmation checks
    - no signing
    - no transaction creation
    - no rebroadcast
    """

    def __init__(self, root=None, rpc=None, stale_after_seconds=900):
        self.recovery = PendingTransactionRecovery(root=root, rpc=rpc)
        self.root = self.recovery.root
        self.runtime = self.recovery.runtime
        self.status_path = self.runtime / "pending_reconciliation_status.json"
        self.stale_after_seconds = int(stale_after_seconds)

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _age_seconds(self, iso_ts):
        if not iso_ts:
            return None
        try:
            ts = datetime.fromisoformat(str(iso_ts).replace("Z", "+00:00"))
            return max(0.0, (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds())
        except Exception:
            return None

    def inspect(self):
        rows = self.recovery.pending()
        enriched = []
        stale = 0
        for row in rows:
            item = dict(row)
            age = self._age_seconds(item.get("created_at"))
            item["age_seconds"] = age
            item["stale"] = bool(age is not None and age >= self.stale_after_seconds)
            if item["stale"]:
                stale += 1
            enriched.append(item)

        return {
            "success": True,
            "status": "pending_reconciliation_inspection",
            "pending_count": len(enriched),
            "stale_count": stale,
            "stale_after_seconds": self.stale_after_seconds,
            "pending": enriched,
            "rebroadcast_performed": False,
        }

    def run_once(self, limit=100):
        before = self.inspect()
        reconcile = self.recovery.reconcile_all(limit=limit)
        after = self.inspect()

        result = {
            "success": True,
            "status": "pending_reconciliation_worker_complete",
            "timestamp": self._now(),
            "before": before,
            "reconcile": reconcile,
            "after": after,
            "rebroadcast_performed": False,
        }
        self.status_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
        return result
