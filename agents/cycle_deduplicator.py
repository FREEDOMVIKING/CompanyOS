#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"
HISTORY = MEM / "autonomy_cycle_history.json"

def load() -> dict[str, Any]:
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except Exception:
        return {"entries": {}}

def save(data: dict[str, Any]) -> None:
    HISTORY.write_text(json.dumps(data, indent=2), encoding="utf-8")

def fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def recently_seen(payload: Any, ttl_seconds: int) -> bool:
    data = load()
    entries = data.setdefault("entries", {})
    fp = fingerprint(payload)
    now = time.time()

    stale = [k for k, ts in entries.items() if now - float(ts) > ttl_seconds]
    for key in stale:
        entries.pop(key, None)

    seen = fp in entries
    entries[fp] = now
    save(data)
    return seen

if __name__ == "__main__":
    print(json.dumps({"success": True, "status": "cycle_deduplicator_ready"}, indent=2))
