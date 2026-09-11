#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path.home() / "companyos"
STATE = ROOT / ".companyos_runtime" / "self_build" / "state.json"

def main():
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok":False,"reason":f"{type(exc).__name__}: {exc}"}))
        return 1

    checks = {
        "state_exists": STATE.exists(),
        "plan_recorded": bool(data.get("plan_id")),
        "tests_recorded": isinstance(data.get("tests"), list),
        "gates_preserved": data.get("hard_gates_preserved") is True,
    }

    out = {
        "ok": all(checks.values()),
        "checks": checks,
        "last_build_ok": data.get("ok"),
        "rolled_back": data.get("rolled_back"),
        "title": data.get("title"),
    }

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
