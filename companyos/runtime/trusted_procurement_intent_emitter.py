from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
LOCAL_RT=ROOT/".companyos_runtime"
PRT=RT/"procurement"

REQUIREMENTS=PRT/"requirements.jsonl"
SOURCING=PRT/"sourcing_requests.jsonl"
EMITTED=PRT/"trusted_emitted_requirements.jsonl"
DECLARATIONS=PRT/"procurement_dependency_declarations.jsonl"
STATE=PRT/"trusted_procurement_emitter_state.json"
LATEST=PRT/"trusted_procurement_emitter_latest.json"
HISTORY=PRT/"trusted_procurement_emitter_history.jsonl"

VERSION="V66.14"
MAX_FILES=800
MAX_FILE_BYTES=2_000_000
MAX_AGE_SECONDS=30*86400

TRUSTED_ROOT_NAMES=(
    "profit_first_candidates",
    "canonical_research_outputs",
    "reports",
    "live_validation",
    "venture_launch",
    "ventures",
    "generated_products",
    "specialist_evidence",
    "venture_blockers",
)

VENTURE_KEYS=(
    "venture_id","candidate_id","project_id","orchestration_id","goal_id","opportunity_id","id",
)

# Structured keys that explicitly declare an external dependency.
ITEM_KEYS=(
    "required_resource","required_resources",
    "required_service","required_services",
    "required_tool","required_tools",
    "required_subscription","required_subscriptions",
    "external_dependency","external_dependencies",
    "purchase_requirement","purchase_requirements",
    "procurement_requirement","procurement_requirements",
    "inventory_requirement","inventory_requirements",
    "hosting_requirement","hosting_requirements",
    "domain_requirement","domain_requirements",
)

TEXT_KEYS=(
    "next_action","action","objective","milestone","description",
    "requirement","need","dependency","plan",
)

ACQUIRE_PATTERNS=(
    r"\bmust\s+(?:buy|purchase|subscribe|rent|lease|hire|acquire|obtain)\b",
    r"\bneed(?:s)?\s+to\s+(?:buy|purchase|subscribe|rent|lease|hire|acquire|obtain)\b",
    r"\brequires?\s+(?:an?\s+)?(?:external\s+)?(?:vendor|supplier|subscription|hosting|domain|service|tool|equipment|inventory|license|api)\b",
    r"\b(?:buy|purchase|subscribe\s+to|rent|lease|hire|acquire|obtain)\s+(?:an?\s+|the\s+)?[a-z0-9]",
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

VENDOR_KEYS=("vendor","supplier","provider","merchant","seller","contractor")
PRICE_USD_KEYS=(
    "quoted_price_usd","cost_usd","price_usd","capital_required_usd",
    "funding_required_usd","payment_amount_usd","budget_usd",
)
PRICE_SOL_KEYS=("amount_sol","price_sol","capital_required_sol","payment_amount_sol")
RECIPIENT_KEYS=("recipient","recipient_address","wallet_address","payment_address","pay_to","solana_recipient")
PROFIT_KEYS=("expected_profit_usd","expected_profit_30d","projected_profit_30d","expected_profit")
PROB_KEYS=("probability","probability_estimate","success_probability","probability_of_profit")
EVIDENCE_KEYS=("evidence_count","verified_evidence_count")


def clean(v: Any) -> str:
    return " ".join(str(v or "").split()).strip()


def first(d: dict[str,Any],keys) -> Any:
    for k in keys:
        v=d.get(k)
        if v not in (None,"",[],{}):
            return v
    return None


def num(d: dict[str,Any],keys) -> float|None:
    v=first(d,keys)
    if v is None:
        return None
    try:return float(v)
    except Exception:return None


def prob(d: dict[str,Any]) -> float|None:
    x=num(d,PROB_KEYS)
    if x is None:return None
    if 1 < x <= 100:x/=100
    return x if 0<=x<=1 else None


def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def load_json(path: Path,default: Any) -> Any:
    try:return json.loads(path.read_text())
    except Exception:return default


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
            if os.path.exists(tmp):os.unlink(tmp)
        except Exception:pass


def self_ref(text: str) -> bool:
    q=clean(text).lower()
    return any(x in q for x in SELF_REFERENTIAL)


def category_for(text: str,key: str="") -> str:
    q=(key+" "+clean(text)).lower()
    if "domain" in q:return "domain"
    if any(x in q for x in ("hosting","server","cloud hosting","deploy host")):return "hosting"
    if any(x in q for x in ("inventory","wholesale","supplier","stock product")):return "inventory_product"
    if any(x in q for x in ("contractor","freelancer","labor service","hire service")):return "contractor_service"
    if any(x in q for x in ("equipment","rental","material","machine","tool rental")):return "materials_equipment"
    if any(x in q for x in ("advertising","paid ads","campaign spend","ad spend")):return "advertising"
    return "software_api"


def trusted_roots() -> list[Path]:
    out=[]
    for base in (RT,LOCAL_RT):
        for name in TRUSTED_ROOT_NAMES:
            p=base/name
            if p.exists():
                out.append(p)
    return out


def recent_files() -> list[Path]:
    now=time.time()
    found=[]
    seen=set()
    for root in trusted_roots():
        try: paths=list(root.rglob("*"))
        except Exception: continue
        for p in paths:
            if not p.is_file() or p.suffix.lower() not in {".json",".jsonl"}:
                continue
            try: st=p.stat()
            except Exception: continue
            if st.st_size>MAX_FILE_BYTES or now-st.st_mtime>MAX_AGE_SECONDS:
                continue
            rp=str(p.resolve())
            if rp in seen:continue
            seen.add(rp)
            found.append(p)
    found.sort(key=lambda p:p.stat().st_mtime,reverse=True)
    return found[:MAX_FILES]


def walk(obj: Any,depth: int=0):
    if depth>8:return
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            yield from walk(v,depth+1)
    elif isinstance(obj,list):
        for v in obj:
            yield from walk(v,depth+1)


def records(path: Path):
    try:text=path.read_text(errors="ignore")
    except Exception:return
    if path.suffix.lower()==".jsonl":
        for n,line in enumerate(text.splitlines(),1):
            try:o=json.loads(line)
            except Exception:continue
            for d in walk(o):
                yield d,f"{path}:{n}"
    else:
        try:o=json.loads(text)
        except Exception:return
        for d in walk(o):
            yield d,str(path)


def venture_id(d: dict[str,Any]) -> str|None:
    v=first(d,VENTURE_KEYS)
    return clean(v) if v not in (None,"") else None


def text_acquisition_intent(text: str) -> bool:
    if not text or self_ref(text):return False
    q=clean(text).lower()
    return any(re.search(p,q) for p in ACQUIRE_PATTERNS)


def normalize_item(value: Any) -> list[str]:
    out=[]
    if isinstance(value,str):
        s=clean(value)
        if s and not self_ref(s):out.append(s)
    elif isinstance(value,list):
        for x in value:
            out.extend(normalize_item(x))
    elif isinstance(value,dict):
        for k in ("item","name","resource","service","tool","requirement","need","description"):
            if k in value:
                out.extend(normalize_item(value[k]))
                if out:break
    return out


def explicit_items(d: dict[str,Any]) -> list[tuple[str,str]]:
    out=[]
    for k in ITEM_KEYS:
        if k not in d:continue
        for item in normalize_item(d.get(k)):
            out.append((k,item))
    for k in TEXT_KEYS:
        v=d.get(k)
        if isinstance(v,str) and text_acquisition_intent(v):
            out.append((k,clean(v)))
    return out


def fingerprint(venture: str,category: str,item: str,source: str) -> str:
    return hashlib.sha256(json.dumps({
        "venture_id":venture,
        "category":category,
        "item":item,
        "source_artifact":source,
    },sort_keys=True,separators=(",",":")).encode()).hexdigest()


def requirement_row(d: dict[str,Any],source: str,key: str,item: str) -> dict[str,Any]|None:
    vid=venture_id(d)
    if not vid:return None
    category=category_for(item,key)

    vendor=first(d,VENDOR_KEYS)
    price_usd=num(d,PRICE_USD_KEYS)
    amount_sol=num(d,PRICE_SOL_KEYS)
    recipient=first(d,RECIPIENT_KEYS)
    expected_profit=num(d,PROFIT_KEYS)
    probability=prob(d)
    ev=num(d,EVIDENCE_KEYS)

    missing=[]
    if not vendor:missing.append("vendor")
    if price_usd is None and amount_sol is None:missing.append("price")
    if not recipient:missing.append("payment_destination")
    if expected_profit is None:missing.append("expected_profit_usd")
    if probability is None:missing.append("probability")
    if ev is None:missing.append("evidence_count")

    fp=fingerprint(vid,category,item,source)
    return {
        "schema":"companyos.procurement_requirement.v2",
        "version":VERSION,
        "requirement_id":"proc-"+fp[:24],
        "created_at_unix":time.time(),
        "venture_id":vid,
        "category":category,
        "item":item,
        "vendor":clean(vendor) if vendor else None,
        "price_usd":price_usd,
        "amount_sol":amount_sol,
        "recipient":clean(recipient) if recipient else None,
        "expected_profit_usd":expected_profit,
        "probability_estimate":probability,
        "evidence_count":int(ev) if ev is not None else None,
        "source_artifact":source,
        "source_field":key,
        "procurement_intent_explicit":True,
        "trusted_source":True,
        "missing_fields":missing,
        "status":"SOURCING_REQUIRED" if missing else "READY_FOR_CAPITAL",
        "fabricated_fields":[],
        "fingerprint":fp,
    }


def sourcing_row(req: dict[str,Any]) -> dict[str,Any]:
    return {
        "schema":"companyos.procurement_sourcing_request.v2",
        "version":VERSION,
        "sourcing_request_id":"source-"+req["fingerprint"][:24],
        "created_at_unix":time.time(),
        "venture_id":req["venture_id"],
        "category":req["category"],
        "item":req["item"],
        "known_vendor":req.get("vendor"),
        "known_price_usd":req.get("price_usd"),
        "known_amount_sol":req.get("amount_sol"),
        "known_payment_destination":req.get("recipient"),
        "source_artifact":req["source_artifact"],
        "source_field":req["source_field"],
        "missing_fields":list(req.get("missing_fields") or []),
        "status":"OPEN",
        "procurement_intent_explicit":True,
        "trusted_source":True,
    }


def existing_fingerprints() -> set[str]:
    out=set()
    for path in (REQUIREMENTS,EMITTED):
        if not path.exists():continue
        for line in path.read_text(errors="ignore").splitlines():
            try:x=json.loads(line)
            except Exception:continue
            fp=x.get("fingerprint")
            if fp:out.add(str(fp))
            elif x.get("venture_id") and x.get("item") and x.get("source_artifact"):
                out.add(fingerprint(
                    clean(x.get("venture_id")),
                    clean(x.get("category")),
                    clean(x.get("item")),
                    clean(x.get("source_artifact")),
                ))
    return out


def scan_once() -> dict[str,Any]:
    seen=existing_fingerprints()
    scanned_files=0
    scanned_records=0
    explicit_dependencies=0
    created=[]
    duplicates=0
    ventures_seen=set()

    for path in recent_files():
        scanned_files+=1
        for d,source in records(path):
            scanned_records+=1
            vid=venture_id(d)
            if vid:ventures_seen.add(vid)
            items=explicit_items(d)
            if not items:continue
            for key,item in items:
                explicit_dependencies+=1
                req=requirement_row(d,source,key,item)
                if not req:continue
                if req["fingerprint"] in seen:
                    duplicates+=1
                    continue
                seen.add(req["fingerprint"])
                append_jsonl(REQUIREMENTS,req)
                append_jsonl(EMITTED,req)
                append_jsonl(SOURCING,sourcing_row(req))
                created.append({
                    "requirement_id":req["requirement_id"],
                    "venture_id":req["venture_id"],
                    "category":req["category"],
                    "item":req["item"],
                    "source_field":req["source_field"],
                    "source_artifact":req["source_artifact"],
                })

    report={
        "version":VERSION,
        "mode":"trusted_procurement_intent_emission",
        "scanned_files":scanned_files,
        "scanned_records":scanned_records,
        "ventures_seen":len(ventures_seen),
        "explicit_dependencies_found":explicit_dependencies,
        "requirements_created":len(created),
        "duplicates_skipped":duplicates,
        "created":created,
        "rules":{
            "generic_opportunity_words_create_purchase":False,
            "explicit_structured_dependency_required":True,
            "explicit_acquisition_language_allowed":True,
            "vendor_fabrication":False,
            "price_fabrication":False,
            "payment_destination_fabrication":False,
            "amount_fabrication":False,
            "zero_requirements_is_valid":True,
        },
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,{"timestamp_unix":time.time(),**report})
    return report


def active_venture_ids() -> list[str]:
    out=[]
    for p in recent_files():
        for d,_ in records(p):
            v=venture_id(d)
            if v and v not in out:out.append(v)
            if len(out)>=200:return out
    return out


def declaration_requests_once(max_tasks: int=10) -> dict[str,Any]:
    # Ask planning to declare external dependencies explicitly. This does NOT
    # create a purchase. The emitter still requires the resulting trusted
    # venture artifact to contain a concrete dependency before emitting one.
    q=AutonomousTaskQueue()
    existing=set()
    if DECLARATIONS.exists():
        for line in DECLARATIONS.read_text(errors="ignore").splitlines():
            try:x=json.loads(line)
            except Exception:continue
            if x.get("venture_id"):existing.add(str(x["venture_id"]))

    created=[]
    for vid in active_venture_ids():
        if vid in existing:continue
        try:
            t=q.enqueue(
                task_type="planning",
                priority=78,
                max_attempts=3,
                idempotency_key=f"procurement-dependency-declaration:{vid}",
                payload={
                    "venture_id":vid,
                    "objective":(
                        "Review the venture's actual next milestones and explicitly declare whether "
                        "any external resource must be acquired. If none is required, say "
                        "procurement_required=false. If procurement is required, name the exact "
                        "resource/service/tool/subscription/domain/hosting/inventory dependency and "
                        "why the milestone cannot proceed without it."
                    ),
                    "required_output":{
                        "procurement_required":"boolean",
                        "required_resources":"list of exact external resources only when required",
                        "reason":"specific milestone dependency",
                    },
                    "constraints":[
                        "do not create a purchase merely because a vendor or price exists",
                        "do not invent a vendor",
                        "do not invent a price",
                        "do not invent a payment destination",
                        "prefer existing internal capability when sufficient",
                    ],
                    "stage":"planning",
                },
            )
            row={
                "timestamp_unix":time.time(),
                "venture_id":vid,
                "task_id":t.task_id,
                "state":t.state,
                "creates_purchase":False,
            }
            append_jsonl(DECLARATIONS,row)
            created.append(row)
        except Exception as exc:
            created.append({"venture_id":vid,"error":f"{type(exc).__name__}:{exc}"})
        if len(created)>=max(1,int(max_tasks)):break

    return {
        "version":VERSION,
        "declaration_tasks_created_or_reused":len(created),
        "tasks":created,
    }


def status() -> dict[str,Any]:
    return {
        "version":VERSION,
        "latest":load_json(LATEST,{}),
        "requirements_file":str(REQUIREMENTS),
        "emitted_file":str(EMITTED),
        "declarations_file":str(DECLARATIONS),
    }


def loop(interval: int):
    while True:
        try:
            r=scan_once()
            if r["requirements_created"]==0:
                declaration_requests_once(5)
            print(json.dumps({
                "ts":time.time(),
                "explicit_dependencies_found":r["explicit_dependencies_found"],
                "requirements_created":r["requirements_created"],
            },sort_keys=True),flush=True)
        except Exception as exc:
            print(json.dumps({"ts":time.time(),"error":f"{type(exc).__name__}:{exc}"},sort_keys=True),flush=True)
        time.sleep(max(60,int(interval)))


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("once")
    sub.add_parser("status")
    d=sub.add_parser("declarations")
    d.add_argument("--max-tasks",type=int,default=10)
    lp=sub.add_parser("loop")
    lp.add_argument("--interval",type=int,default=120)
    args=ap.parse_args()

    if args.cmd=="once":
        print(json.dumps(scan_once(),indent=2,sort_keys=True))
    elif args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True))
    elif args.cmd=="declarations":
        print(json.dumps(declaration_requests_once(args.max_tasks),indent=2,sort_keys=True))
    elif args.cmd=="loop":
        loop(args.interval)


if __name__=="__main__":
    main()
