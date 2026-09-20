from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from companyos.connectors_live.engine import ConnectorEngine
from companyos.runtime import live_drl_strategy_governor as governor

ROOT = (Path.home() / "companyos").resolve()
RT = Path.home() / ".companyos_runtime"
ROUTER_RT = RT / "live_external_execution"
STATE = ROUTER_RT / "state.json"
LATEST = ROUTER_RT / "latest.json"
HISTORY = ROUTER_RT / "history.jsonl"

ROUTER_RT.mkdir(parents=True, exist_ok=True)

VERSION = "V66.00"

# IMPORTANT:
# CompanyOS's current live connector registry contains real SMTP and hosting
# executors. Banking/crypto are handoff connectors in the current CompanyOS
# registry and therefore are intentionally not treated as live money-moving
# executors here.
ACTION_POLICY = {
    ("hosting", "deploy_production"): "public_deployment",
    ("hosting", "deploy_preview"): "public_deployment",
    ("hosting", "deploy_worker"): "public_deployment",
    ("smtp", "send_email"): "unsolicited_outreach",
}

# Never import or call wallet/trading code from other projects.
FORBIDDEN_CONNECTORS = {"banking", "crypto"}
FORBIDDEN_ACTIONS = {
    "transfer_funds",
    "sign_transaction",
    "execute_signed_swap",
    "wallet_transaction",
    "buy_ads",
    "purchase_ads",
    "rotate_secret",
    "change_credential",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n")
    tmp.replace(path)


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(obj, sort_keys=True, default=str) + "\n")


def authority() -> dict[str, Any]:
    # Read the user's current switch state exactly as configured.
    return dict(governor.LIVE_AUTHORITY)


def activation_state() -> dict[str, Any]:
    st = load_json(STATE, {})
    if not st:
        st = {
            "version": VERSION,
            "activated_at_unix": time.time(),
            "activated_at": now_iso(),
            "execution_mode": "live_external",
            "baseline_only_new_actions": True,
            "executed_action_ids": [],
            "skipped_action_ids": [],
        }
        save_json(STATE, st)
    return st


def engine() -> ConnectorEngine:
    return ConnectorEngine()


def health() -> dict[str, Any]:
    eng = engine()
    h = eng.health()
    auth = authority()
    connectors = h.get("connectors") or {}

    live = {}
    for name in ("hosting", "smtp", "rest_api", "domains", "banking", "crypto"):
        item = dict(connectors.get(name) or {})
        item["live_ready"] = bool(
            item.get("enabled")
            and item.get("configured")
            and item.get("dry_run") is False
        )
        if name in FORBIDDEN_CONNECTORS:
            item["router_execution_enabled"] = False
            item["router_reason"] = "not_a_verified_live_companyos_money_executor"
        else:
            item["router_execution_enabled"] = item["live_ready"]
        live[name] = item

    return {
        "version": VERSION,
        "mode": "live_external",
        "authority": auth,
        "connectors": live,
        "verified_live_actions": [
            {
                "connector": c,
                "action": a,
                "authority_switch": sw,
                "authority_enabled": bool(auth.get(sw)),
            }
            for (c, a), sw in ACTION_POLICY.items()
        ],
        "wallet_trading_project_imported": False,
        "financial_executor_status": "not_wired_current_companyos_registry_is_handoff_only",
        "paid_ads_executor_status": "not_wired_no_verified_live_ads_connector",
    }


def _parse_created_at(value: Any) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _executed_ids(eng: ConnectorEngine) -> set[str]:
    path = eng.runtime / "executions.json"
    rows = load_json(path, [])
    if not isinstance(rows, list):
        return set()
    return {
        str(x.get("action_id"))
        for x in rows
        if isinstance(x, dict) and x.get("action_id")
    }


def _approved_ids(eng: ConnectorEngine) -> set[str]:
    path = eng.runtime / "approvals.json"
    rows = load_json(path, [])
    if not isinstance(rows, list):
        return set()
    return {
        str(x.get("action_id"))
        for x in rows
        if isinstance(x, dict) and x.get("action_id") and x.get("approved")
    }


def classify(action: dict[str, Any], h: dict[str, Any]) -> tuple[bool, str]:
    connector = str(action.get("connector") or "")
    act = str(action.get("action") or "")
    auth = h.get("authority") or {}

    if connector in FORBIDDEN_CONNECTORS or act in FORBIDDEN_ACTIONS:
        return False, "money_or_credential_action_not_wired"

    switch = ACTION_POLICY.get((connector, act))
    if not switch:
        return False, "action_not_in_verified_live_external_allowlist"

    if not bool(auth.get(switch)):
        return False, f"authority_switch_off:{switch}"

    ch = (h.get("connectors") or {}).get(connector) or {}
    if not ch.get("live_ready"):
        return False, f"connector_not_live_ready:{connector}"

    return True, "authorized_live_external"


def pending_actions() -> list[dict[str, Any]]:
    eng = engine()
    rows = load_json(eng.runtime / "actions.json", [])
    if not isinstance(rows, list):
        return []

    st = activation_state()
    activated = float(st.get("activated_at_unix") or 0.0)
    executed = _executed_ids(eng)

    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        aid = str(row.get("action_id") or "")
        if not aid or aid in executed:
            continue
        created = _parse_created_at(row.get("created_at"))
        # Do not unexpectedly execute old/demo/stale queued actions that
        # existed before this live router was activated.
        if created and created < activated:
            continue
        out.append(row)
    return out


def process_once(max_actions: int = 5) -> dict[str, Any]:
    eng = engine()
    h = health()
    st = activation_state()
    rows = pending_actions()
    results = []
    approved = _approved_ids(eng)

    for row in rows[: max(1, int(max_actions))]:
        aid = str(row.get("action_id"))
        ok, reason = classify(row, h)

        item = {
            "action_id": aid,
            "connector": row.get("connector"),
            "action": row.get("action"),
            "authorized": ok,
            "reason": reason,
            "executed": False,
            "result": None,
        }

        if not ok:
            results.append(item)
            continue

        # The user's enabled LIVE_AUTHORITY switch acts as standing approval
        # only for the verified live action allowlist above.
        if aid not in approved:
            eng.approve(aid, approved_by="live_drl_authority")
            item["auto_approved"] = True
        else:
            item["auto_approved"] = False

        result = eng.execute(aid)
        item["result"] = result
        item["executed"] = bool(result and result.get("ok"))
        results.append(item)

        append_jsonl(HISTORY, {
            "timestamp_unix": time.time(),
            "timestamp": now_iso(),
            **item,
        })

        if item["executed"]:
            ids = list(st.get("executed_action_ids") or [])
            if aid not in ids:
                ids.append(aid)
            st["executed_action_ids"] = ids[-1000:]

    st["last_process_at_unix"] = time.time()
    st["last_process_at"] = now_iso()
    st["last_results"] = results
    save_json(STATE, st)

    report = {
        "version": VERSION,
        "mode": "live_external",
        "pending_seen": len(rows),
        "processed": len(results),
        "executed": sum(1 for x in results if x["executed"]),
        "results": results,
        "health": h,
    }
    save_json(LATEST, report)
    return report


def queue_deployment(project_name: str, website_path: str, risk: str = "high") -> dict[str, Any]:
    if not authority().get("public_deployment"):
        return {"ok": False, "status": "authority_switch_off:public_deployment"}

    payload = {
        "project_name": project_name,
        "website_path": website_path,
    }
    row = engine().queue("hosting", "deploy_production", payload, risk=risk)
    return {"ok": True, "queued": row}


def queue_email(to: str, subject: str, body: str, risk: str = "high") -> dict[str, Any]:
    if not authority().get("unsolicited_outreach"):
        return {"ok": False, "status": "authority_switch_off:unsolicited_outreach"}

    # No bulk list expansion here. Each queued message remains an auditable
    # action with its own action_id.
    payload = {"to": to, "subject": subject, "body": body}
    row = engine().queue("smtp", "send_email", payload, risk=risk)
    return {"ok": True, "queued": row}


def status() -> dict[str, Any]:
    st = activation_state()
    h = health()
    return {
        "version": VERSION,
        "mode": "live_external",
        "router_state": st,
        "pending_new_actions": len(pending_actions()),
        "health": h,
    }


def loop(interval: int = 60, max_actions: int = 5) -> None:
    while True:
        try:
            r = process_once(max_actions=max_actions)
            print(json.dumps({
                "ts": time.time(),
                "mode": r["mode"],
                "pending_seen": r["pending_seen"],
                "processed": r["processed"],
                "executed": r["executed"],
            }, sort_keys=True), flush=True)
        except Exception as e:
            print(json.dumps({
                "ts": time.time(),
                "error": f"{type(e).__name__}: {e}",
            }, sort_keys=True), flush=True)
        time.sleep(max(15, int(interval)))


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health")
    sub.add_parser("status")
    p = sub.add_parser("process")
    p.add_argument("--max-actions", type=int, default=5)

    d = sub.add_parser("queue-deploy")
    d.add_argument("--project", required=True)
    d.add_argument("--path", required=True)

    e = sub.add_parser("queue-email")
    e.add_argument("--to", required=True)
    e.add_argument("--subject", required=True)
    e.add_argument("--body-file", required=True)

    lp = sub.add_parser("loop")
    lp.add_argument("--interval", type=int, default=60)
    lp.add_argument("--max-actions", type=int, default=5)

    args = ap.parse_args()

    if args.cmd == "health":
        print(json.dumps(health(), indent=2, sort_keys=True))
    elif args.cmd == "status":
        print(json.dumps(status(), indent=2, sort_keys=True))
    elif args.cmd == "process":
        print(json.dumps(process_once(args.max_actions), indent=2, sort_keys=True))
    elif args.cmd == "queue-deploy":
        print(json.dumps(queue_deployment(args.project, args.path), indent=2, sort_keys=True))
    elif args.cmd == "queue-email":
        body = Path(args.body_file).read_text()
        print(json.dumps(queue_email(args.to, args.subject, body), indent=2, sort_keys=True))
    elif args.cmd == "loop":
        loop(args.interval, args.max_actions)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
