from __future__ import annotations
from pathlib import Path
from typing import Any
import json, time, uuid

class SchedulerFinancialActivityLedgerBridge:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home()/".companyos_runtime"/"autonomy_activity_ledger")
        self.root.mkdir(parents=True, exist_ok=True)

    def record(self, *, intent: dict[str, Any], result: dict[str, Any]) -> Path:
        now=time.time()
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "scheduler_financial_action",
            "created_at_unix": now,
            "intent": intent,
            "result": result,
        }
        day=time.strftime("%Y-%m-%d", time.localtime(now))
        d=self.root/day
        d.mkdir(parents=True, exist_ok=True)
        p=d/f"{int(now*1000)}_{payload['event_id']}.json"
        tmp=p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        tmp.replace(p)
        return p
