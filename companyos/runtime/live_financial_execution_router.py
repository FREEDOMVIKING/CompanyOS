from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from companyos.connectors_live.engine import ConnectorEngine
from companyos.runtime import live_drl_strategy_governor as governor

RT = Path.home()/".companyos_runtime"
FRT = RT/"live_financial_execution"
STATE = FRT/"state.json"
LATEST = FRT/"latest.json"
HISTORY = FRT/"history.jsonl"
FRT.mkdir(parents=True, exist_ok=True)

VERSION = "V66.01"


def load_json(path: Path, default: Any):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any):
    tmp = path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str)+"\n")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str, Any]):
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, default=str)+"\n")


def activation_state():
    st = load_json(STATE,{})
    if not st:
        st = {
            "version": VERSION,
            "mode": "live_financial",
            "activated_at_unix": time.time(),
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "baseline_only_new_actions": True,
        }
        save_json(STATE,st)
    return st


def auth():
    return dict(governor.LIVE_AUTHORITY)


def engine():
    return ConnectorEngine()


def crypto_health():
    eng = engine()
    conn = eng.registry.get("crypto")
    if not conn:
        return {"ok":False,"status":"crypto_connector_missing"}
    h = conn.health()
    return {
        "ok": True,
        "authority": {
            "financial_actions": bool(auth().get("financial_actions")),
            "wallet_transactions": bool(auth().get("wallet_transactions")),
        },
        "connector": h,
        "live_ready": bool(
            h.get("enabled")
            and h.get("configured")
            and h.get("dry_run") is False
        ),
    }


def _ts(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z","+00:00")).timestamp()
    except Exception:
        return 0.0


def _executed(eng):
    rows=load_json(eng.runtime/"executions.json",[])
    return {
        str(x.get("action_id")) for x in rows
        if isinstance(x,dict) and x.get("action_id")
    }


def pending():
    eng=engine()
    rows=load_json(eng.runtime/"actions.json",[])
    st=activation_state()
    cutoff=float(st.get("activated_at_unix") or 0)
    done=_executed(eng)
    out=[]
    for x in rows if isinstance(rows,list) else []:
        if not isinstance(x,dict): continue
        if x.get("connector")!="crypto": continue
        aid=str(x.get("action_id") or "")
        if not aid or aid in done: continue
        created=_ts(x.get("created_at"))
        if created and created < cutoff: continue
        out.append(x)
    return out


def classify(action):
    h=crypto_health()
    if not h.get("live_ready"):
        return False,"crypto_connector_not_live_ready"

    act=str(action.get("action") or "")
    a=h.get("authority") or {}

    if act=="get_balance":
        return bool(a.get("financial_actions")),"financial_actions_authority_required"

    if act in {"transfer_funds","transfer_sol"}:
        if not a.get("wallet_transactions"):
            return False,"wallet_transactions_authority_required"

        conn=engine().registry.get("crypto")
        pre=conn.preflight_transfer(action.get("payload") or {})
        if not pre.get("ok"):
            return False,pre.get("status") or "transfer_preflight_failed"
        return True,"wallet_transfer_preflight_pass"

    return False,"unsupported_financial_action"


def process_once(max_actions=3):
    eng=engine()
    rows=pending()
    results=[]

    for row in rows[:max(1,int(max_actions))]:
        aid=str(row.get("action_id"))
        ok,reason=classify(row)
        item={
            "action_id":aid,
            "action":row.get("action"),
            "authorized":ok,
            "reason":reason,
            "executed":False,
        }

        if ok:
            if row.get("approval_required"):
                eng.approve(aid,approved_by="live_drl_financial_authority")
            result=eng.execute(aid)
            item["result"]=result
            item["executed"]=bool(result and result.get("ok"))

        results.append(item)
        append_jsonl(HISTORY,{
            "timestamp_unix":time.time(),
            "timestamp":datetime.now(timezone.utc).isoformat(),
            **item,
        })

    report={
        "version":VERSION,
        "mode":"live_financial",
        "pending_seen":len(rows),
        "processed":len(results),
        "executed":sum(1 for x in results if x["executed"]),
        "results":results,
        "health":crypto_health(),
    }
    save_json(LATEST,report)
    return report


def status():
    return {
        "version":VERSION,
        "mode":"live_financial",
        "state":activation_state(),
        "health":crypto_health(),
        "pending_new_financial_actions":len(pending()),
    }


def loop(interval=60,max_actions=3):
    while True:
        try:
            r=process_once(max_actions)
            print(json.dumps({
                "ts":time.time(),
                "mode":"live_financial",
                "pending":r["pending_seen"],
                "processed":r["processed"],
                "executed":r["executed"],
            },sort_keys=True),flush=True)
        except Exception as exc:
            print(json.dumps({
                "ts":time.time(),
                "mode":"live_financial",
                "error":f"{type(exc).__name__}:{exc}",
            },sort_keys=True),flush=True)
        time.sleep(max(15,int(interval)))


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status")
    sub.add_parser("health")
    p=sub.add_parser("process")
    p.add_argument("--max-actions",type=int,default=3)
    lp=sub.add_parser("loop")
    lp.add_argument("--interval",type=int,default=60)
    lp.add_argument("--max-actions",type=int,default=3)
    args=ap.parse_args()

    if args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="health":
        print(json.dumps(crypto_health(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="process":
        print(json.dumps(process_once(args.max_actions),indent=2,sort_keys=True,default=str))
    elif args.cmd=="loop":
        loop(args.interval,args.max_actions)


if __name__=="__main__":
    main()
