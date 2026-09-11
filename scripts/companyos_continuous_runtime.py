#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
STATE = RUNTIME / "continuous_runtime_state.json"
LEDGER = RUNTIME / "continuous_runtime_ledger.jsonl"
LOCK = RUNTIME / "continuous_runtime.lock"
STOP = RUNTIME / "continuous_runtime.stop"
ASSETS = RUNTIME / "managed_assets.json"
RECONCILE = RUNTIME / "deployment_reconciliation.json"
OPPORTUNITY_INBOX = RUNTIME / "ceo_opportunity_inbox"

RUNTIME.mkdir(parents=True, exist_ok=True)
OPPORTUNITY_INBOX.mkdir(parents=True, exist_ok=True)

_shutdown = False

def on_signal(signum, frame):
    global _shutdown
    _shutdown = True

signal.signal(signal.SIGTERM, on_signal)
signal.signal(signal.SIGINT, on_signal)

def now():
    return time.time()

def emit(obj, code=0):
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def ledger(event):
    event = dict(event)
    event.setdefault("ts", now())
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

def load_json(path, default):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return default

def save_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

def run_cmd(cmd, payload, timeout=600):
    try:
        p = subprocess.run(
            cmd,
            input=json.dumps(payload),
            text=True,
            shell=True,
            capture_output=True,
            timeout=timeout,
            cwd=str(ROOT),
            env=os.environ.copy(),
        )
        try:
            data = json.loads((p.stdout or "").strip()) if (p.stdout or "").strip() else {}
        except Exception:
            data = {
                "ok": False,
                "reason": "non_json_response",
                "stdout": (p.stdout or "")[:6000],
                "stderr": (p.stderr or "")[:6000],
                "returncode": p.returncode,
            }
        return data, p.returncode
    except Exception as exc:
        return {
            "ok": False,
            "reason": "command_exception",
            "error": f"{type(exc).__name__}: {exc}",
        }, 1

def http_check(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"CompanyOS-Runtime/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(1500).decode("utf-8","replace")
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"

def reconcile_assets():
    registry = load_json(ASSETS, {"assets":[]})
    assets = registry.get("assets") if isinstance(registry, dict) else []
    if not isinstance(assets, list):
        assets = []

    report = {
        "checked_at": now(),
        "assets_total": len(assets),
        "healthy": [],
        "pending": [],
        "unhealthy": [],
    }

    changed = False
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        vid = asset.get("venture_id")
        health = asset.get("health_url")
        if not health:
            report["pending"].append(vid)
            continue

        status, body = http_check(health)
        asset["last_health_http"] = status
        asset["last_health_check_at"] = now()

        if status == 200:
            asset["last_known_health"] = "healthy"
            if asset.get("status") == "deployed_pending_public_verification":
                asset["status"] = "live_verified"
                changed = True
            report["healthy"].append(vid)
        else:
            asset["last_known_health"] = "unhealthy"
            asset["last_health_error"] = body[:1000]
            report["unhealthy"].append(vid)

    if changed:
        registry["assets"] = assets
        save_json(ASSETS, registry)

    save_json(RECONCILE, report)
    ledger({
        "event":"deployment_reconciliation_complete",
        "healthy":len(report["healthy"]),
        "pending":len(report["pending"]),
        "unhealthy":len(report["unhealthy"]),
    })
    return report

def dedupe_inbox():
    seen = {}
    duplicates = []
    for p in sorted(OPPORTUNITY_INBOX.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        key = str(d.get("opportunity_id") or d.get("venture_id") or d.get("id") or p.stem).strip().lower()
        if not key:
            continue
        if key in seen:
            duplicates.append(str(p))
            try:
                p.rename(p.with_suffix(".duplicate.json"))
            except Exception:
                pass
        else:
            seen[key] = str(p)
    if duplicates:
        ledger({"event":"opportunity_duplicates_suppressed","count":len(duplicates),"files":duplicates[:50]})
    return {"unique":len(seen),"duplicates":len(duplicates)}

def run_ceo_cycle():
    cmd = os.getenv("COMPANYOS_CEO_OPERATING_LOOP_CMD","").strip()
    if not cmd:
        return {"ok":False,"reason":"missing_ceo_operating_loop_cmd"}, 2
    return run_cmd(cmd, {"action":"cycle"}, timeout=900)

def state_defaults():
    return {
        "started_at": now(),
        "last_cycle_started": None,
        "last_cycle_finished": None,
        "cycles_total": 0,
        "cycles_ok": 0,
        "cycles_failed": 0,
        "consecutive_failures": 0,
        "last_error": None,
        "last_result": None,
        "last_reconciliation": None,
        "status": "idle",
    }

def load_state():
    st = load_json(STATE, state_defaults())
    if not isinstance(st, dict):
        st = state_defaults()
    for k,v in state_defaults().items():
        st.setdefault(k,v)
    return st

def write_lock():
    LOCK.write_text(json.dumps({"pid":os.getpid(),"started_at":now()})+"\n", encoding="utf-8")

def clear_lock():
    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass

def stop_requested():
    return _shutdown or STOP.exists()

def loop():
    state = load_state()
    interval = max(60, int(os.getenv("COMPANYOS_CEO_CYCLE_INTERVAL_SECONDS","900")))
    reconcile_every = max(1, int(os.getenv("COMPANYOS_RECONCILE_EVERY_CYCLES","1")))
    failure_backoff = max(30, int(os.getenv("COMPANYOS_FAILURE_BACKOFF_SECONDS","120")))

    write_lock()
    try:
        if STOP.exists():
            STOP.unlink()

        state["status"] = "running"
        save_json(STATE,state)
        ledger({"event":"continuous_runtime_started","pid":os.getpid(),"interval":interval})

        while not stop_requested():
            state["last_cycle_started"] = now()
            state["status"] = "cycle_running"
            save_json(STATE,state)

            dedupe = dedupe_inbox()
            result, rc = run_ceo_cycle()

            state["cycles_total"] += 1
            state["last_result"] = result
            state["last_cycle_finished"] = now()

            ok = bool(result.get("ok")) and rc == 0
            if ok:
                state["cycles_ok"] += 1
                state["consecutive_failures"] = 0
                state["last_error"] = None
            else:
                state["cycles_failed"] += 1
                state["consecutive_failures"] += 1
                state["last_error"] = result

            reconciliation = None
            if state["cycles_total"] % reconcile_every == 0:
                reconciliation = reconcile_assets()
                state["last_reconciliation"] = reconciliation

            state["status"] = "sleeping" if ok else "backoff"
            save_json(STATE,state)
            ledger({
                "event":"continuous_cycle_complete",
                "ok":ok,
                "cycle":state["cycles_total"],
                "dedupe":dedupe,
                "reconciliation":reconciliation,
            })

            sleep_for = interval if ok else min(interval, failure_backoff * max(1,state["consecutive_failures"]))
            slept = 0
            while slept < sleep_for and not stop_requested():
                time.sleep(min(5, sleep_for - slept))
                slept += min(5, sleep_for - slept)

        state["status"] = "stopped"
        state["stopped_at"] = now()
        save_json(STATE,state)
        ledger({"event":"continuous_runtime_stopped","pid":os.getpid()})
    finally:
        clear_lock()

def one_cycle():
    dedupe = dedupe_inbox()
    result, rc = run_ceo_cycle()
    reconciliation = reconcile_assets()
    out = {
        "ok": bool(result.get("ok")) and rc == 0,
        "dedupe":dedupe,
        "ceo_cycle":result,
        "reconciliation":reconciliation,
    }
    emit(out, 0 if out["ok"] else 1)

def status():
    emit({
        "ok":True,
        "state":load_state(),
        "lock_present":LOCK.exists(),
        "stop_requested":STOP.exists(),
        "reconciliation":load_json(RECONCILE,{}),
    })

def stop():
    STOP.write_text(str(now())+"\n", encoding="utf-8")
    emit({"ok":True,"action":"stop_requested","stop_file":str(STOP)})

if __name__ == "__main__":
    action = (sys.argv[1] if len(sys.argv)>1 else "status").strip().lower()
    if action == "run":
        loop()
    elif action == "once":
        one_cycle()
    elif action == "status":
        status()
    elif action == "stop":
        stop()
    elif action == "reconcile":
        emit({"ok":True,"reconciliation":reconcile_assets()})
    else:
        emit({"ok":False,"reason":"unsupported_action","action":action},2)
