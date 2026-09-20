from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from companyos.connectors_live.engine import ConnectorEngine
from companyos.runtime import live_drl_strategy_governor as governor

RT = Path.home()/".companyos_runtime"
FRT = RT/"finance"
INTENTS = FRT/"capital_intents.jsonl"
DECISIONS = FRT/"capital_decisions.jsonl"
STATE = FRT/"capital_allocator_state.json"
FRT.mkdir(parents=True, exist_ok=True)

VERSION="V66.02"
MIN_EVIDENCE=2
MIN_PROBABILITY=0.20
MIN_EXPECTED_NET_USD=0.01
MAX_OPEN_INTENTS=250


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str,Any]):
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def read_jsonl(path: Path):
    if not path.exists():
        return []
    out=[]
    for line in path.read_text().splitlines():
        try:
            x=json.loads(line)
            if isinstance(x,dict):
                out.append(x)
        except Exception:
            pass
    return out


def authority():
    return dict(governor.LIVE_AUTHORITY)


def crypto():
    return ConnectorEngine().registry["crypto"]


def sol_price():
    c=crypto()
    price,source=c._sol_price_usd()
    return price,source


def submit_intent(
    recipient: str,
    amount_sol: float,
    purpose: str,
    venture_id: str,
    expected_profit_usd: float,
    probability: float,
    evidence_count: int,
    source: str="companyos",
):
    row={
        "intent_id":str(uuid.uuid4()),
        "created_at_unix":time.time(),
        "created_at":now_iso(),
        "status":"PENDING",
        "asset":"SOL",
        "recipient":recipient,
        "amount_sol":float(amount_sol),
        "purpose":str(purpose),
        "venture_id":str(venture_id),
        "expected_profit_usd":float(expected_profit_usd),
        "probability":float(probability),
        "evidence_count":int(evidence_count),
        "source":str(source),
    }
    append_jsonl(INTENTS,row)
    return row


def latest_by_intent():
    rows=read_jsonl(INTENTS)
    latest={}
    for r in rows:
        iid=r.get("intent_id")
        if iid:
            latest[str(iid)]=r
    return latest


def decided_ids():
    out=set()
    for r in read_jsonl(DECISIONS):
        if r.get("intent_id"):
            out.add(str(r["intent_id"]))
    return out


def evaluate(row: dict[str,Any]):
    a=authority()
    if not a.get("financial_actions"):
        return {"eligible":False,"reason":"financial_actions_switch_off"}
    if not a.get("wallet_transactions"):
        return {"eligible":False,"reason":"wallet_transactions_switch_off"}

    required=["recipient","amount_sol","purpose","venture_id","expected_profit_usd","probability","evidence_count"]
    missing=[k for k in required if row.get(k) in (None,"")]
    if missing:
        return {"eligible":False,"reason":"missing_required_fields","missing":missing}

    try:
        amount_sol=float(row["amount_sol"])
        profit=float(row["expected_profit_usd"])
        prob=float(row["probability"])
        evidence=int(row["evidence_count"])
    except Exception:
        return {"eligible":False,"reason":"invalid_numeric_fields"}

    if amount_sol <= 0:
        return {"eligible":False,"reason":"nonpositive_amount"}
    if not (0.0 <= prob <= 1.0):
        return {"eligible":False,"reason":"probability_out_of_range"}
    if evidence < MIN_EVIDENCE:
        return {"eligible":False,"reason":"insufficient_evidence","evidence_count":evidence}
    if prob < MIN_PROBABILITY:
        return {"eligible":False,"reason":"probability_below_floor","probability":prob}

    c=crypto()
    pre=c.preflight_transfer({
        "asset":"SOL",
        "to":row["recipient"],
        "amount_sol":amount_sol,
    })
    if not pre.get("ok"):
        return {"eligible":False,"reason":"connector_preflight_failed","preflight":pre}

    amount_usd=pre.get("amount_usd")
    if amount_usd is None:
        price,src=sol_price()
        if not price:
            return {"eligible":False,"reason":"sol_usd_price_unavailable"}
        amount_usd=amount_sol*float(price)
    else:
        src=pre.get("price_source")

    expected_gross=prob*profit
    expected_net=expected_gross-float(amount_usd)
    roi=expected_net/max(float(amount_usd),0.01)

    if expected_net < MIN_EXPECTED_NET_USD:
        return {
            "eligible":False,
            "reason":"negative_or_too_small_expected_net",
            "expected_net_usd":expected_net,
            "expected_gross_usd":expected_gross,
            "capital_cost_usd":amount_usd,
            "expected_roi":roi,
        }

    return {
        "eligible":True,
        "reason":"positive_verified_expected_value",
        "expected_net_usd":expected_net,
        "expected_gross_usd":expected_gross,
        "capital_cost_usd":amount_usd,
        "expected_roi":roi,
        "price_source":src,
        "preflight":pre,
    }


def open_intents():
    latest=latest_by_intent()
    done=decided_ids()
    rows=[]
    for iid,row in latest.items():
        if iid in done:
            continue
        if str(row.get("status","PENDING")).upper()!="PENDING":
            continue
        rows.append(row)
    rows.sort(key=lambda x:float(x.get("created_at_unix") or 0))
    return rows[-MAX_OPEN_INTENTS:]


def rank():
    out=[]
    for row in open_intents():
        ev=evaluate(row)
        out.append({"intent":row,"evaluation":ev})
    out.sort(
        key=lambda x:(
            1 if x["evaluation"].get("eligible") else 0,
            float(x["evaluation"].get("expected_roi") or -999999),
            float(x["evaluation"].get("expected_net_usd") or -999999),
        ),
        reverse=True,
    )
    return out


def allocate_once():
    ranked=rank()
    selected=next((x for x in ranked if x["evaluation"].get("eligible")),None)
    if not selected:
        result={
            "version":VERSION,
            "status":"NO_ELIGIBLE_CAPITAL_INTENT",
            "open_intents":len(ranked),
            "timestamp_unix":time.time(),
        }
        save_json(STATE,result)
        return result

    row=selected["intent"]
    ev=selected["evaluation"]

    eng=ConnectorEngine()
    queued=eng.queue(
        "crypto",
        "transfer_funds",
        {
            "asset":"SOL",
            "to":row["recipient"],
            "amount_sol":float(row["amount_sol"]),
            "purpose":row["purpose"],
            "venture_id":row["venture_id"],
            "capital_intent_id":row["intent_id"],
            "expected_profit_usd":float(row["expected_profit_usd"]),
            "probability":float(row["probability"]),
            "evidence_count":int(row["evidence_count"]),
        },
        risk="high",
    )

    decision={
        "version":VERSION,
        "timestamp_unix":time.time(),
        "timestamp":now_iso(),
        "intent_id":row["intent_id"],
        "venture_id":row["venture_id"],
        "decision":"FUND",
        "evaluation":ev,
        "queued_financial_action":queued,
    }
    append_jsonl(DECISIONS,decision)
    save_json(STATE,{
        "version":VERSION,
        "status":"CAPITAL_INTENT_FUNDED_AND_QUEUED",
        "last_decision":decision,
        "timestamp_unix":time.time(),
    })
    return decision


def status():
    rows=rank()
    return {
        "version":VERSION,
        "authority":{
            "financial_actions":bool(authority().get("financial_actions")),
            "wallet_transactions":bool(authority().get("wallet_transactions")),
        },
        "open_intents":len(rows),
        "eligible_intents":sum(1 for x in rows if x["evaluation"].get("eligible")),
        "top_intents":rows[:10],
        "state":load_json(STATE,{}),
    }


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status")
    sub.add_parser("rank")
    sub.add_parser("once")

    q=sub.add_parser("queue-intent")
    q.add_argument("--recipient",required=True)
    q.add_argument("--amount-sol",required=True,type=float)
    q.add_argument("--purpose",required=True)
    q.add_argument("--venture-id",required=True)
    q.add_argument("--expected-profit-usd",required=True,type=float)
    q.add_argument("--probability",required=True,type=float)
    q.add_argument("--evidence-count",required=True,type=int)

    args=ap.parse_args()
    if args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="rank":
        print(json.dumps(rank(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="once":
        print(json.dumps(allocate_once(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="queue-intent":
        print(json.dumps(submit_intent(
            args.recipient,args.amount_sol,args.purpose,args.venture_id,
            args.expected_profit_usd,args.probability,args.evidence_count,
            source="cli",
        ),indent=2,sort_keys=True,default=str))

if __name__=="__main__":
    main()
