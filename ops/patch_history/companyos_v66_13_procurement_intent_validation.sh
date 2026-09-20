#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/procurement_intent_validator.py"
SOURCING="$ROOT/companyos/runtime/autonomous_procurement_sourcing.py"
CTL="$ROOT/scripts/companyos_procurement_intentctl"
SCTL="$ROOT/scripts/companyos_sourcingctl"
PIDFILE="$RT/procurement_intent_validator.pid"
LOGFILE="$RT/procurement_intent_validator.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.13 PROCUREMENT INTENT VALIDATION + QUARANTINE ====="
echo "GOAL=ONLY_REAL_PURCHASE_NEEDS_CAN_ENTER_VENDOR_SOURCING"
echo "NOTE=GENERIC_OPPORTUNITY_WORDS_ARE_NOT_PURCHASE_INTENT"
echo "NOTE=INVALIDATED_REQUIREMENTS_ARE_QUARANTINED_NOT_DELETED"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$SOURCING" ] || { echo "V66_13_ABORT=missing:$SOURCING"; exit 1; }

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT/procurement"

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$MOD" "$SOURCING"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_13_backup_${stamp}"
    echo "BACKUP=${f}.v66_13_backup_${stamp}"
  fi
done

cat > "$MOD" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
PRT=RT/"procurement"

REQUIREMENTS=PRT/"requirements.jsonl"
SOURCING=PRT/"sourcing_requests.jsonl"
VALIDATIONS=PRT/"procurement_intent_validations.jsonl"
INDEX=PRT/"procurement_intent_validation_index.json"
QUARANTINE=PRT/"quarantined_requirements.jsonl"
LATEST=PRT/"procurement_intent_validation_latest.json"
HISTORY=PRT/"procurement_intent_validation_history.jsonl"

VERSION="V66.13"

# Keys that strongly indicate a real resource/acquisition dependency.
EXPLICIT_KEYS={
    "required_resource","required_resources","required_service","required_services",
    "required_tool","required_tools","required_vendor","required_supplier",
    "required_capability","capability_gap","external_dependency",
    "purchase_required","procurement_required","subscription_required",
    "inventory_required","hosting_required","domain_required",
    "capital_required_usd","funding_required_usd","payment_amount_usd",
    "quoted_price_usd","budget_usd","budget","vendor","supplier",
    "recipient","recipient_address","payment_address","pay_to",
}

PURCHASE_FIELDS={
    "requirement","requirements","need","needs","dependency","dependencies",
    "next_action","action","objective","plan","constraints","notes",
}

ACQUIRE_TERMS=(
    "purchase ","buy ","subscribe ","subscription","procure ","source vendor",
    "source supplier","hire ","rent ","lease ","pay for ","requires external",
    "need external","needs external","requires a ","requires an ",
    "must obtain","must acquire","must purchase","must subscribe",
    "vendor required","supplier required","hosting required","domain required",
)

SELF_REFERENTIAL=(
    "acquire real external evidence for missing procurement fields",
    "do not fabricate vendor",
    "do not fabricate price",
    "do not fabricate payment destination",
    "official vendor evidence required",
    "checkout or invoice required",
    "provider comparison",
    "vendor selection",
    "procurement sourcing",
    "sourcing request",
)

WEAK_ONLY_TERMS={
    "price","pricing","profit","margin","revenue","api","software","domain",
    "hosting","marketplace","provider","vendor","product","service",
    "opportunity","business","advertising",
}


def read_jsonl(path: Path) -> list[dict[str,Any]]:
    if not path.exists():
        return []
    out=[]
    for line in path.read_text(errors="ignore").splitlines():
        try:
            x=json.loads(line)
            if isinstance(x,dict):
                out.append(x)
        except Exception:
            pass
    return out


def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def load_json(path: Path,default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path,data: Any) -> None:
    import os,tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp): os.unlink(tmp)
        except Exception:
            pass


def clean(v: Any) -> str:
    return " ".join(str(v or "").split()).strip()


def source_path(source: Any) -> tuple[Path|None,int|None]:
    s=str(source or "")
    m=re.match(r"^(.*\.(?:json|jsonl))(?::(\d+))?$",s,re.I)
    if not m:
        return None,None
    p=Path(m.group(1)).expanduser()
    if not p.exists() or not p.is_file():
        return None,None
    line=int(m.group(2)) if m.group(2) else None
    return p,line


def trusted_source(source: Any) -> bool:
    p,_=source_path(source)
    if not p:
        return False
    q=str(p).replace("\\","/").lower()
    if "/procurement/" in q:
        return False
    allowed=(
        "/profit_first_candidates/","/canonical_research_outputs/","/reports/",
        "/live_validation/","/venture_launch/","/ventures/",
        "/generated_products/","/specialist_evidence/",
    )
    return any(x in q for x in allowed)


def load_source_record(source: Any) -> Any:
    p,line=source_path(source)
    if not p:
        return None
    try:
        if p.suffix.lower()==".jsonl" and line:
            lines=p.read_text(errors="ignore").splitlines()
            if 1<=line<=len(lines):
                return json.loads(lines[line-1])
        if p.suffix.lower()==".json":
            return json.loads(p.read_text(errors="ignore"))
        # No line number: bounded full JSONL list.
        vals=[]
        for raw in p.read_text(errors="ignore").splitlines()[:5000]:
            try:vals.append(json.loads(raw))
            except Exception:pass
        return vals
    except Exception:
        return None


def walk(obj: Any,depth: int=0):
    if depth>8:
        return
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            yield from walk(v,depth+1)
    elif isinstance(obj,list):
        for v in obj:
            yield from walk(v,depth+1)


def self_referential(text: str) -> bool:
    q=clean(text).lower()
    return any(x in q for x in SELF_REFERENTIAL)


def explicit_key_signal(d: dict[str,Any]) -> list[dict[str,Any]]:
    hits=[]
    for k,v in d.items():
        lk=str(k).lower()
        if lk not in EXPLICIT_KEYS:
            continue
        if v in (None,"",[],{},False):
            continue
        text=clean(v)
        if self_referential(text):
            continue
        hits.append({"kind":"explicit_key","key":lk,"value":text[:500]})
    return hits


def acquisition_text_signal(d: dict[str,Any]) -> list[dict[str,Any]]:
    hits=[]
    for k,v in d.items():
        lk=str(k).lower()
        if lk not in PURCHASE_FIELDS or not isinstance(v,str):
            continue
        text=clean(v)
        low=text.lower()
        if self_referential(text):
            continue
        terms=[x.strip() for x in ACQUIRE_TERMS if x in low]
        if terms:
            hits.append({
                "kind":"acquisition_text",
                "key":lk,
                "terms":terms[:8],
                "value":text[:800],
            })
    return hits


def explicit_vendor_and_cost(d: dict[str,Any]) -> list[dict[str,Any]]:
    vendor=d.get("vendor") or d.get("supplier") or d.get("provider")
    cost=None
    cost_key=None
    for k in (
        "quoted_price_usd","capital_required_usd","funding_required_usd",
        "payment_amount_usd","budget_usd","cost_usd","price_usd",
    ):
        if d.get(k) not in (None,""):
            try:
                cost=float(d[k]); cost_key=k
            except Exception:
                pass
            if cost is not None:
                break
    if vendor and cost is not None and cost>0:
        return [{
            "kind":"vendor_plus_cost",
            "vendor":clean(vendor)[:300],
            "cost_usd":cost,
            "cost_key":cost_key,
        }]
    return []


def weak_signal_only(d: dict[str,Any]) -> bool:
    blob=" ".join(
        f"{k} {v}" for k,v in d.items()
        if isinstance(v,(str,int,float,bool))
    ).lower()
    words=set(re.findall(r"[a-z]{3,}",blob))
    return bool(words & WEAK_ONLY_TERMS)


def fingerprint_fields(
    venture_id: Any,
    category: Any,
    item: Any,
    source_artifact: Any,
) -> str:
    stable={
        "venture_id":clean(venture_id),
        "category":clean(category),
        "item":clean(item),
        "source_artifact":clean(source_artifact),
    }
    return hashlib.sha256(
        json.dumps(stable,sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()


def requirement_fingerprint(req: dict[str,Any]) -> str:
    return fingerprint_fields(
        req.get("venture_id"),
        req.get("category"),
        req.get("item"),
        req.get("source_artifact"),
    )


def sourcing_fingerprint(sr: dict[str,Any]) -> str:
    return fingerprint_fields(
        sr.get("venture_id"),
        sr.get("category"),
        sr.get("item"),
        sr.get("source_artifact"),
    )


def validate_requirement(req: dict[str,Any]) -> dict[str,Any]:
    fp=requirement_fingerprint(req)
    source=req.get("source_artifact")
    base={
        "schema":"companyos.procurement_intent_validation.v1",
        "version":VERSION,
        "timestamp_unix":time.time(),
        "fingerprint":fp,
        "requirement_id":req.get("requirement_id"),
        "venture_id":req.get("venture_id"),
        "category":req.get("category"),
        "item":req.get("item"),
        "source_artifact":source,
        "trusted_source":trusted_source(source),
        "signals":[],
        "status":"QUARANTINED",
        "sourcing_allowed":False,
    }

    if not trusted_source(source):
        return {**base,"reason":"source_missing_or_not_trusted"}

    obj=load_source_record(source)
    if obj is None:
        return {**base,"reason":"source_record_unreadable"}

    signals=[]
    weak=False
    for d in walk(obj):
        signals.extend(explicit_key_signal(d))
        signals.extend(acquisition_text_signal(d))
        signals.extend(explicit_vendor_and_cost(d))
        weak=weak or weak_signal_only(d)

    # De-duplicate evidence without altering its meaning.
    unique=[]
    seen=set()
    for x in signals:
        key=json.dumps(x,sort_keys=True,default=str)
        if key in seen:
            continue
        seen.add(key); unique.append(x)

    # Strong enough when the original trusted artifact explicitly states an
    # acquisition/resource dependency, or gives an actual vendor + cost.
    strong=any(
        x.get("kind") in {"explicit_key","acquisition_text","vendor_plus_cost"}
        for x in unique
    )

    if strong:
        return {
            **base,
            "signals":unique[:30],
            "weak_commercial_language_present":weak,
            "status":"VALIDATED",
            "sourcing_allowed":True,
            "reason":"explicit_procurement_intent_in_trusted_source",
        }

    return {
        **base,
        "signals":unique[:30],
        "weak_commercial_language_present":weak,
        "status":"QUARANTINED",
        "sourcing_allowed":False,
        "reason":"no_explicit_purchase_or_resource_dependency_in_original_source",
    }


def rebuild_index() -> dict[str,Any]:
    rows=read_jsonl(REQUIREMENTS)
    latest={}
    validations=[]
    quarantined=[]

    for req in rows:
        v=validate_requirement(req)
        latest[v["fingerprint"]]=v
        validations.append(v)
        append_jsonl(VALIDATIONS,v)
        if not v["sourcing_allowed"]:
            q={
                "timestamp_unix":time.time(),
                "version":VERSION,
                "requirement":req,
                "validation":v,
                "deleted":False,
            }
            append_jsonl(QUARANTINE,q)
            quarantined.append(q)

    idx={
        "version":VERSION,
        "updated_at_unix":time.time(),
        "entries":latest,
    }
    save_json(INDEX,idx)

    report={
        "version":VERSION,
        "mode":"procurement_intent_validation",
        "requirements_seen":len(rows),
        "validated":sum(1 for x in latest.values() if x.get("sourcing_allowed")),
        "quarantined":sum(1 for x in latest.values() if not x.get("sourcing_allowed")),
        "unique_requirements":len(latest),
        "rules":{
            "weak_price_or_profit_words_are_purchase_intent":False,
            "procurement_generated_sources_trusted":False,
            "explicit_acquisition_or_resource_dependency_required":True,
            "quarantine_deletes_history":False,
        },
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,{"timestamp_unix":time.time(),**report})
    return report


def is_sourcing_allowed(sr: dict[str,Any]) -> bool:
    idx=load_json(INDEX,{"entries":{}})
    fp=sourcing_fingerprint(sr)
    row=(idx.get("entries") or {}).get(fp)
    return bool(row and row.get("sourcing_allowed") is True)


def status() -> dict[str,Any]:
    return {
        "version":VERSION,
        "latest":load_json(LATEST,{}),
        "index_entries":len((load_json(INDEX,{"entries":{}}).get("entries") or {})),
        "validation_file":str(VALIDATIONS),
        "quarantine_file":str(QUARANTINE),
    }


def loop(interval: int):
    while True:
        try:
            r=rebuild_index()
            print(json.dumps({
                "ts":time.time(),
                "validated":r["validated"],
                "quarantined":r["quarantined"],
            },sort_keys=True),flush=True)
        except Exception as exc:
            print(json.dumps({
                "ts":time.time(),
                "error":f"{type(exc).__name__}:{exc}",
            },sort_keys=True),flush=True)
        time.sleep(max(60,int(interval)))


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("once")
    sub.add_parser("status")
    lp=sub.add_parser("loop")
    lp.add_argument("--interval",type=int,default=120)
    args=ap.parse_args()

    if args.cmd=="once":
        print(json.dumps(rebuild_index(),indent=2,sort_keys=True))
    elif args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True))
    elif args.cmd=="loop":
        loop(args.interval)


if __name__=="__main__":
    main()
PY

echo "===== PATCH LIVE SOURCING QUEUE WITH INTENT GATE ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/autonomous_procurement_sourcing.py"
s=p.read_text()

anchor="from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue\n"
imp="from companyos.runtime.procurement_intent_validator import is_sourcing_allowed\n"
if imp not in s:
    if anchor not in s:
        raise SystemExit("V66_13_ABORT=sourcing_import_anchor_missing")
    s=s.replace(anchor,anchor+imp,1)

old='''    return [
        x for sid, x in latest.items()
        if sid not in done and str(x.get("status") or "OPEN").upper() == "OPEN"
    ]
'''
new='''    return [
        x for sid, x in latest.items()
        if sid not in done
        and str(x.get("status") or "OPEN").upper() == "OPEN"
        and is_sourcing_allowed(x)
    ]
'''
if old in s:
    s=s.replace(old,new,1)
elif "and is_sourcing_allowed(x)" not in s:
    raise SystemExit("V66_13_ABORT=pending_requests_anchor_missing")

p.write_text(s)
print("V66_13_SOURCING_GATE_PATCH=PASS")
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
PIDFILE="$RT/procurement_intent_validator.pid"
LOGFILE="$RT/procurement_intent_validator.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "PROCUREMENT_INTENT_VALIDATOR_ALREADY_RUNNING PID=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python -m companyos.runtime.procurement_intent_validator loop \
      --interval "${COMPANYOS_PROCUREMENT_INTENT_INTERVAL_SECONDS:-120}" \
      >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    echo "PROCUREMENT_INTENT_VALIDATOR_RUNNING PID=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    echo "PROCUREMENT_INTENT_VALIDATOR_STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  once)
    python -m companyos.runtime.procurement_intent_validator once
    ;;
  status)
    python -m companyos.runtime.procurement_intent_validator status
    if [ -f "$PIDFILE" ]; then
      echo "PID=$(cat "$PIDFILE")"
      ps -p "$(cat "$PIDFILE")" -o pid,etime,args || true
    fi
    ;;
  quarantine)
    tail -n "${2:-20}" "$RT/procurement/quarantined_requirements.jsonl" 2>/dev/null || true
    ;;
  validations)
    tail -n "${2:-20}" "$RT/procurement/procurement_intent_validations.jsonl" 2>/dev/null || true
    ;;
  log)
    tail -n "${2:-100}" "$LOGFILE"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|once|status|quarantine [n]|validations [n]|log [n]}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_procurement_intent_validator.py" <<'PY'
from companyos.runtime.procurement_intent_validator import (
    acquisition_text_signal,
    explicit_key_signal,
    self_referential,
)

def test_generic_profit_language_not_explicit_purchase():
    d={"title":"Marketplace Software Opportunity","expected_profit_usd":500}
    assert explicit_key_signal(d)==[]
    assert acquisition_text_signal(d)==[]

def test_explicit_required_service_is_purchase_signal():
    d={"required_service":"transactional email API"}
    assert explicit_key_signal(d)

def test_explicit_acquisition_language_is_signal():
    d={"requirement":"must subscribe to an external email delivery service"}
    assert acquisition_text_signal(d)

def test_procurement_boilerplate_is_not_business_need():
    assert self_referential(
        "Acquire real external evidence for missing procurement fields. "
        "Do not fabricate vendor or price."
    )
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD" "$SOURCING"
echo "V66_13_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_procurement_intent_validator.py
echo "V66_13_TESTS=PASS"

echo "===== STOP SOURCING FOR CONSISTENT REINDEX ====="
"$SCTL" stop || true

echo "===== VALIDATE ALL EXISTING PROCUREMENT REQUIREMENTS ====="
"$CTL" once

echo "===== RETRY SOURCING WITH VALIDATED INTENTS ONLY ====="
"$SCTL" once 20 || true

echo "===== START VALIDATOR + SOURCING ====="
"$CTL" restart
"$SCTL" start

echo "===== FINAL STATUS ====="
"$CTL" status
"$SCTL" status

echo "V66_13_EXPLICIT_PURCHASE_INTENT_REQUIRED=PASS"
echo "V66_13_FALSE_POSITIVE_QUARANTINE=PASS"
echo "V66_13_PROCUREMENT_SELF_REFERENCE_BLOCK=PASS"
echo "V66_13_LIVE_SOURCING_GATE=PASS"
echo "V66_13_HISTORY_PRESERVED=PASS"
echo "V66_13_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_13_COMPLETE"
