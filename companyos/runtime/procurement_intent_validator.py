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
