#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "venture_queue"
LEDGER = RUNTIME / "venture_queue_ledger.jsonl"
STATE = RUNTIME / "venture_queue_state.json"
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

def emit(obj, code=0):
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def ledger(event):
    event = dict(event)
    event.setdefault("ts", time.time())
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

def load_state():
    try:
        d = json.loads(STATE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {"processed":[]}
    except Exception:
        return {"processed":[]}

def save_state(d):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(STATE)

def queue_item_path(item_id):
    return QUEUE_DIR / f"{item_id}.json"

try:
    req = json.load(sys.stdin)
except Exception as e:
    emit({"ok":False,"reason":"invalid_json_input","error":str(e)},2)

action = str(req.get("action") or "").strip().lower()
state = load_state()
state.setdefault("processed", [])

if action == "enqueue":
    item = req.get("item")
    if not isinstance(item, dict):
        emit({"ok":False,"reason":"missing_item"},2)

    item_id = str(item.get("venture_id") or item.get("id") or "").strip()
    if not item_id:
        emit({"ok":False,"reason":"missing_venture_id"},2)

    item.setdefault("queue_status", "queued")
    item.setdefault("queued_at", time.time())

    p = queue_item_path(item_id)
    p.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ledger({"event":"venture_enqueued","venture_id":item_id,"path":str(p)})
    emit({"ok":True,"action":"enqueue","venture_id":item_id,"path":str(p)})

if action == "list":
    items = []
    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            d["_path"] = str(p)
            items.append(d)
        except Exception:
            pass
    emit({"ok":True,"action":"list","count":len(items),"items":items})

if action == "process_one":
    launcher = os.getenv("COMPANYOS_AUTONOMOUS_VENTURE_LAUNCH_CMD","").strip()
    if not launcher:
        emit({"ok":False,"reason":"missing_launcher_command"},2)

    candidates = []
    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if str(d.get("queue_status","queued")) != "queued":
            continue
        candidates.append((p,d))

    if not candidates:
        emit({"ok":True,"action":"process_one","processed":False,"reason":"queue_empty"})

    p, item = candidates[0]
    vid = str(item.get("venture_id") or item.get("id") or p.stem)

    approved = item.get("approved") is True
    launch_ready = item.get("launch_ready") is True
    auto_launch = item.get("auto_launch") is True

    if not approved or not launch_ready or not auto_launch:
        item["queue_status"] = "blocked"
        item["blocked_reason"] = {
            "approved": approved,
            "launch_ready": launch_ready,
            "auto_launch": auto_launch,
        }
        p.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        ledger({"event":"venture_blocked","venture_id":vid,"reason":item["blocked_reason"]})
        emit({"ok":True,"action":"process_one","processed":False,"venture_id":vid,"blocked":True,"reason":item["blocked_reason"]})

    payload = {
        "live": True,
        "venture": {
            "venture_id": vid,
            "name": item.get("name") or vid,
            "approved": True,
            "launch_ready": True,
            "tagline": item.get("tagline") or "Built by CompanyOS",
            "description": item.get("description") or "",
            "contact": item.get("contact") or "",
            "worker_name": item.get("worker_name") or f"venture-{vid}",
        }
    }

    ledger({"event":"venture_processing_started","venture_id":vid})

    try:
        proc = subprocess.run(
            launcher,
            input=json.dumps(payload),
            text=True,
            shell=True,
            capture_output=True,
            timeout=360,
            cwd=str(ROOT),
            env=os.environ.copy()
        )
    except Exception as e:
        item["queue_status"] = "failed"
        item["last_error"] = f"{type(e).__name__}: {e}"
        p.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        ledger({"event":"venture_processing_failed","venture_id":vid,"error":item["last_error"]})
        emit({"ok":False,"venture_id":vid,"reason":"launcher_exception","error":item["last_error"]},1)

    try:
        result = json.loads((proc.stdout or "").strip())
    except Exception:
        result = {
            "ok":False,
            "reason":"launcher_non_json",
            "stdout":(proc.stdout or "")[:5000],
            "stderr":(proc.stderr or "")[:5000],
            "returncode":proc.returncode
        }

    if result.get("ok") and proc.returncode == 0:
        item["queue_status"] = "launched"
        item["launched_at"] = time.time()
        item["public_url"] = result.get("public_url")
        item["launch_receipt"] = result.get("receipt")
        if vid not in state["processed"]:
            state["processed"].append(vid)
        save_state(state)
        p.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        ledger({
            "event":"venture_processing_completed",
            "venture_id":vid,
            "public_url":item.get("public_url"),
            "receipt":item.get("launch_receipt")
        })
        emit({
            "ok":True,
            "action":"process_one",
            "processed":True,
            "venture_id":vid,
            "public_url":item.get("public_url"),
            "launch_result":result
        })

    item["queue_status"] = "failed"
    item["last_result"] = result
    p.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ledger({"event":"venture_processing_failed","venture_id":vid,"result":result})
    emit({"ok":False,"venture_id":vid,"launch_result":result},1)

if action == "process_all":
    processed = []
    blocked = []
    failed = []

    while True:
        sub = subprocess.run(
            [sys.executable, __file__],
            input=json.dumps({"action":"process_one"}),
            text=True,
            capture_output=True,
            timeout=420,
            env=os.environ.copy()
        )
        try:
            result = json.loads((sub.stdout or "").strip())
        except Exception:
            result = {"ok":False,"reason":"process_one_non_json","stdout":(sub.stdout or "")[:3000]}

        if result.get("reason") == "queue_empty":
            break
        if result.get("processed"):
            processed.append(result.get("venture_id"))
            continue
        if result.get("blocked"):
            blocked.append(result.get("venture_id"))
            continue
        failed.append(result)
        break

    emit({
        "ok": len(failed) == 0,
        "action":"process_all",
        "processed":processed,
        "blocked":blocked,
        "failed":failed
    }, 0 if not failed else 1)

emit({"ok":False,"reason":"unsupported_action","action":action},2)
