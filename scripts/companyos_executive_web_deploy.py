#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
RECEIPTS = RUNTIME / "deployment_receipts"
LEDGER = RUNTIME / "executive_deployment_ledger.jsonl"
RECEIPTS.mkdir(parents=True, exist_ok=True)
LEDGER.parent.mkdir(parents=True, exist_ok=True)

def emit(obj: dict, code: int = 0) -> None:
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def append_ledger(event: dict) -> None:
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")

def save_receipt(obj: dict) -> str:
    ts = int(time.time())
    path = RECEIPTS / f"executive_deploy_{ts}.json"
    latest = RECEIPTS / "executive_deploy_latest.json"
    text = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    return str(path)

try:
    req = json.load(sys.stdin)
except Exception as exc:
    emit({"ok": False, "reason": "invalid_json_input", "error": str(exc)}, 2)

name = str(req.get("name") or req.get("script_name") or "").strip()
source = req.get("source")
live = req.get("live") is True

if not name:
    emit({"ok": False, "reason": "missing_name"}, 2)
if not isinstance(source, str) or not source.strip():
    emit({"ok": False, "reason": "missing_source"}, 2)

provider = os.environ.get("COMPANYOS_REAL_WEB_DEPLOY_PROVIDER_CMD", "").strip()
if not provider:
    provider = f'python "{ROOT}/scripts/companyos_cf_web_deploy_provider.py"'

provider_req = {
    "action": "deploy",
    "script_name": name,
    "source": source,
    "live": live,
}

started = time.time()
append_ledger({
    "ts": started,
    "event": "executive_deployment_started",
    "name": name,
    "live": live,
})

try:
    proc = subprocess.run(
        provider,
        input=json.dumps(provider_req),
        text=True,
        shell=True,
        capture_output=True,
        timeout=180,
        cwd=str(ROOT),
        env=os.environ.copy(),
    )
except Exception as exc:
    out = {
        "ok": False,
        "stage": "provider_execution",
        "error": f"{type(exc).__name__}: {exc}",
        "name": name,
        "live": live,
    }
    out["receipt"] = save_receipt(out)
    append_ledger({
        "ts": time.time(),
        "event": "executive_deployment_failed",
        "name": name,
        "stage": "provider_execution",
    })
    emit(out, 1)

stdout = (proc.stdout or "").strip()
stderr = (proc.stderr or "").strip()

try:
    provider_out = json.loads(stdout) if stdout else {}
except Exception:
    provider_out = {
        "ok": False,
        "reason": "provider_returned_non_json",
        "stdout": stdout[:5000],
        "stderr": stderr[:5000],
        "returncode": proc.returncode,
    }

out = {
    "ok": bool(provider_out.get("ok")) and proc.returncode == 0,
    "stage": "provider_complete",
    "name": name,
    "live": live,
    "provider": provider_out,
    "provider_returncode": proc.returncode,
    "stderr": stderr[:5000],
    "elapsed_seconds": round(time.time() - started, 3),
}
out["receipt"] = save_receipt(out)

append_ledger({
    "ts": time.time(),
    "event": "executive_deployment_completed" if out["ok"] else "executive_deployment_failed",
    "name": name,
    "live": live,
    "public_url": provider_out.get("public_url"),
    "receipt": out["receipt"],
})

emit(out, 0 if out["ok"] else 1)
