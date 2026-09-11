#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "execution_eligibility_config.json"
READINESS = MEM / "readiness2_report.json"
STATE = MEM / "execution_eligibility_state.json"
REPORT = MEM / "execution_eligibility_report.json"
HEALTH = MEM / "execution_eligibility_health.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def evaluate() -> dict[str, Any]:
    cfg = load(CFG, {})
    readiness = load(READINESS, {})

    ready = readiness.get("decision") == "ready"
    matrix = {
        "internal_read_only": ready and bool(cfg.get("allow_internal_read_only", True)),
        "internal_reversible": ready and bool(cfg.get("allow_internal_reversible", True)),
        "external_read_only": ready and bool(cfg.get("allow_external_read_only", True)),
        "external_write": False,
        "customer_contact": False,
        "publication": False,
        "spending": False,
        "destructive_actions": False,
        "credential_export": False,
        "private_key_export": False
    }

    report = {
        "generated_at": now(),
        "readiness_decision": readiness.get("decision"),
        "system_ready": ready,
        "eligibility": matrix,
        "blocked_categories": [k for k, v in matrix.items() if not v],
        "allowed_categories": [k for k, v in matrix.items() if v]
    }

    save(REPORT, report)
    save(STATE, {
        "last_evaluated_at": now(),
        "system_ready": ready,
        "allowed_count": len(report["allowed_categories"]),
        "blocked_count": len(report["blocked_categories"])
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "system_ready": ready
    })

    return {
        "success": True,
        "status": "execution_eligibility_evaluated",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "execution_eligibility_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "run":
        result = evaluate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["run", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
