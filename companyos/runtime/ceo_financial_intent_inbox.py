from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import time

from companyos.runtime.ceo_financial_intent_producer import produce_ceo_financial_intent

ROOT = Path("companyos_runtime/ceo_financial_intents")
INBOX = ROOT / "inbox"
PROCESSED = ROOT / "processed"
REJECTED = ROOT / "rejected"
for p in (INBOX, PROCESSED, REJECTED):
    p.mkdir(parents=True, exist_ok=True)

def process_inbox(max_items: int = 10) -> dict[str, Any]:
    summary = {"seen": 0, "queued": 0, "rejected": 0, "errors": 0, "last_error": None}
    for p in sorted(INBOX.glob("*.json"))[:max_items]:
        summary["seen"] += 1
        try:
            data = json.loads(p.read_text())
            result = produce_ceo_financial_intent(data)
            target = PROCESSED if result.accepted else REJECTED
            wrapped = {
                "source_file": p.name,
                "processed_at": time.time(),
                "intent": data,
                "result": result.__dict__,
            }
            out = target / p.name
            tmp = out.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(wrapped, indent=2, sort_keys=True, default=str) + "\n")
            tmp.replace(out)
            p.unlink(missing_ok=True)
            summary["queued" if result.accepted else "rejected"] += 1
        except Exception as exc:
            summary["errors"] += 1
            summary["last_error"] = f"{type(exc).__name__}:{str(exc)[:200]}"
    return summary
