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
INBOX = RUNTIME / "ceo_opportunity_inbox"
PLANS = RUNTIME / "ceo_venture_plans"
STATE = RUNTIME / "ceo_operating_state.json"
LEDGER = RUNTIME / "ceo_operating_ledger.jsonl"

for p in (INBOX, PLANS):
    p.mkdir(parents=True, exist_ok=True)

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
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def save_state(d):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(STATE)

def run_queue(payload):
    cmd = os.getenv("COMPANYOS_CEO_VENTURE_QUEUE_CMD", "").strip()
    if not cmd:
        return {"ok": False, "reason": "missing_queue_command"}, 2
    try:
        p = subprocess.run(
            cmd,
            input=json.dumps(payload),
            text=True,
            shell=True,
            capture_output=True,
            timeout=480,
            cwd=str(ROOT),
            env=os.environ.copy(),
        )
        try:
            out = json.loads((p.stdout or "").strip()) if (p.stdout or "").strip() else {}
        except Exception:
            out = {
                "ok": False,
                "reason": "queue_non_json",
                "stdout": (p.stdout or "")[:5000],
                "stderr": (p.stderr or "")[:5000],
            }
        return out, p.returncode
    except Exception as exc:
        return {"ok": False, "reason": "queue_exception", "error": f"{type(exc).__name__}: {exc}"}, 1

def normalize_opportunity(raw):
    oid = str(raw.get("opportunity_id") or raw.get("venture_id") or raw.get("id") or "").strip()
    name = str(raw.get("name") or raw.get("title") or "").strip()
    if not oid or not name:
        return None

    score = float(raw.get("score", 0) or 0)
    risk = str(raw.get("risk") or "medium").strip().lower()
    estimated_cost = float(raw.get("estimated_cost", 0) or 0)

    # Deterministic policy layer. The discovery system may propose opportunities,
    # but only candidates satisfying the configured launch policy can auto-advance.
    min_score = float(os.getenv("COMPANYOS_CEO_AUTO_LAUNCH_MIN_SCORE", "80"))
    max_cost = float(os.getenv("COMPANYOS_CEO_AUTO_LAUNCH_MAX_COST", "250"))
    allowed_risks = {
        x.strip().lower()
        for x in os.getenv("COMPANYOS_CEO_AUTO_LAUNCH_ALLOWED_RISKS", "low,medium").split(",")
        if x.strip()
    }

    policy_ok = score >= min_score and estimated_cost <= max_cost and risk in allowed_risks

    return {
        "venture_id": oid,
        "name": name,
        "tagline": str(raw.get("tagline") or "Built by CompanyOS").strip(),
        "description": str(raw.get("description") or "").strip(),
        "contact": str(raw.get("contact") or "").strip(),
        "score": score,
        "risk": risk,
        "estimated_cost": estimated_cost,
        "approved": bool(raw.get("approved") is True and policy_ok),
        "launch_ready": bool(raw.get("launch_ready") is True),
        "auto_launch": bool(raw.get("auto_launch") is True and policy_ok),
        "policy_ok": policy_ok,
        "source": raw.get("source"),
    }

try:
    req = json.load(sys.stdin)
except Exception as exc:
    emit({"ok": False, "reason": "invalid_json_input", "error": str(exc)}, 2)

action = str(req.get("action") or "").strip().lower()
state = load_state()
state.setdefault("cycles", 0)
state.setdefault("processed_opportunities", [])
state.setdefault("launched_ventures", [])

if action == "submit_opportunity":
    op = req.get("opportunity")
    if not isinstance(op, dict):
        emit({"ok": False, "reason": "missing_opportunity"}, 2)

    norm = normalize_opportunity(op)
    if not norm:
        emit({"ok": False, "reason": "invalid_opportunity_identity"}, 2)

    path = INBOX / f"{norm['venture_id']}.json"
    path.write_text(json.dumps(op, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ledger({
        "event": "opportunity_submitted",
        "venture_id": norm["venture_id"],
        "score": norm["score"],
        "risk": norm["risk"],
        "estimated_cost": norm["estimated_cost"],
    })
    emit({"ok": True, "action": action, "venture_id": norm["venture_id"], "path": str(path)})

if action == "cycle":
    cycle_started = time.time()
    state["cycles"] += 1
    results = {
        "evaluated": [],
        "queued": [],
        "blocked": [],
        "queue_process": None,
    }

    for path in sorted(INBOX.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        norm = normalize_opportunity(raw)
        if not norm:
            continue

        vid = norm["venture_id"]
        if vid in state["processed_opportunities"]:
            continue

        plan = {
            "venture_id": vid,
            "name": norm["name"],
            "tagline": norm["tagline"],
            "description": norm["description"],
            "contact": norm["contact"],
            "score": norm["score"],
            "risk": norm["risk"],
            "estimated_cost": norm["estimated_cost"],
            "approved": norm["approved"],
            "launch_ready": norm["launch_ready"],
            "auto_launch": norm["auto_launch"],
            "policy_ok": norm["policy_ok"],
            "planned_at": time.time(),
        }

        plan_path = PLANS / f"{vid}.json"
        plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results["evaluated"].append(vid)

        if plan["approved"] and plan["launch_ready"] and plan["auto_launch"]:
            qout, qrc = run_queue({"action": "enqueue", "item": plan})
            if qout.get("ok") and qrc == 0:
                results["queued"].append(vid)
                ledger({"event": "venture_queued_from_ceo_loop", "venture_id": vid, "plan": str(plan_path)})
            else:
                results["blocked"].append({"venture_id": vid, "reason": qout})
        else:
            results["blocked"].append({
                "venture_id": vid,
                "reason": {
                    "policy_ok": plan["policy_ok"],
                    "approved": plan["approved"],
                    "launch_ready": plan["launch_ready"],
                    "auto_launch": plan["auto_launch"],
                },
            })
            ledger({
                "event": "venture_blocked_by_ceo_policy",
                "venture_id": vid,
                "policy_ok": plan["policy_ok"],
                "score": plan["score"],
                "risk": plan["risk"],
                "estimated_cost": plan["estimated_cost"],
            })

        state["processed_opportunities"].append(vid)

    if results["queued"]:
        qout, qrc = run_queue({"action": "process_all"})
        results["queue_process"] = qout
        if qout.get("ok") and qrc == 0:
            for vid in qout.get("processed") or []:
                if vid not in state["launched_ventures"]:
                    state["launched_ventures"].append(vid)

    state["last_cycle_at"] = time.time()
    state["last_cycle_elapsed_seconds"] = round(time.time() - cycle_started, 3)
    save_state(state)

    ledger({
        "event": "ceo_operating_cycle_completed",
        "evaluated": results["evaluated"],
        "queued": results["queued"],
        "blocked_count": len(results["blocked"]),
        "launched_total": len(state["launched_ventures"]),
    })

    emit({
        "ok": True,
        "action": "cycle",
        "results": results,
        "state": state,
    })

if action == "status":
    emit({
        "ok": True,
        "action": "status",
        "state": state,
        "inbox_count": len(list(INBOX.glob("*.json"))),
        "plan_count": len(list(PLANS.glob("*.json"))),
    })

emit({"ok": False, "reason": "unsupported_action", "action": action}, 2)
