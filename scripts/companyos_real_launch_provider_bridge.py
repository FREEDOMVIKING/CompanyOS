#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
AUDIT = RUNTIME / "real_launch_provider_bridge.jsonl"

def emit(obj):
    print(json.dumps(obj, sort_keys=True))

def audit(event):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": time.time(), **event}, sort_keys=True) + "\n")

def main():
    try:
        req = json.load(sys.stdin)
    except Exception as exc:
        emit({"ok": False, "reason": "invalid_json_input", "error": f"{type(exc).__name__}: {exc}"})
        raise SystemExit(2)

    action = str(req.get("action", "")).strip()
    mapping = {
        "check": "COMPANYOS_REAL_DOMAIN_CHECK_PROVIDER_CMD",
        "register": "COMPANYOS_REAL_DOMAIN_REGISTER_PROVIDER_CMD",
        "deploy": "COMPANYOS_REAL_WEB_DEPLOY_PROVIDER_CMD",
        "configure_dns": "COMPANYOS_REAL_DNS_CONFIG_PROVIDER_CMD",
    }
    env_name = mapping.get(action)
    if not env_name:
        out = {"ok": False, "reason": "unknown_action", "action": action}
        audit({"kind": "provider_bridge", "request": req, "response": out})
        emit(out)
        return

    cmd = os.environ.get(env_name, "").strip()
    if not cmd:
        out = {"ok": False, "reason": "provider_command_not_configured", "missing_env": env_name}
        audit({"kind": "provider_bridge", "request": req, "response": out})
        emit(out)
        return

    try:
        p = subprocess.run(cmd, input=json.dumps(req), text=True, shell=True, capture_output=True, timeout=180, cwd=str(ROOT), env=os.environ.copy())
        stdout = (p.stdout or "").strip()
        stderr = (p.stderr or "").strip()
        try:
            out = json.loads(stdout) if stdout else {}
        except Exception:
            out = {"ok": False, "reason": "provider_returned_non_json", "stdout": stdout[-4000:], "stderr": stderr[-4000:], "returncode": p.returncode}
        if not isinstance(out, dict):
            out = {"ok": False, "reason": "provider_returned_non_object", "value": out}
        out.setdefault("returncode", p.returncode)
        if stderr:
            out.setdefault("stderr", stderr[-4000:])
        if p.returncode != 0:
            out["ok"] = False
    except Exception as exc:
        out = {"ok": False, "reason": "provider_command_exception", "error": f"{type(exc).__name__}: {exc}"}

    audit({"kind": "provider_bridge", "action": action, "provider_env": env_name, "request": req, "response": out})
    emit(out)

if __name__ == "__main__":
    main()
