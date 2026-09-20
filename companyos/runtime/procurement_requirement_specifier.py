from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
LOCAL_RT=ROOT/".companyos_runtime"

LATEST=RT/"procurement"/"requirement_specificity_latest.json"
AUDIT=RT/"procurement"/"requirement_specificity_audit.jsonl"
LATEST.parent.mkdir(parents=True,exist_ok=True)

VERSION="V66.11"

GENERIC={
    "requirement","requirements","procurement","software","api","software api",
    "software_api","service","services","provider","vendor","supplier",
    "domain","hosting","advertising","inventory","product","contractor",
    "materials","equipment","opportunity","marketplace","platform",
}

CONTEXT_KEYS=(
    "required_capability","capability_gap","required_resource","required_service",
    "integration_required","dependency","dependency_name","use_case",
    "objective","goal","problem","need","requirement","product","service",
    "offer","title","name","business_model","target_customer",
)

ROOT_NAMES=(
    "profit_first_candidates","canonical_research_outputs","reports",
    "live_validation","venture_launch","ventures","generated_products",
    "specialist_evidence",
)

# Never use CompanyOS's own procurement/sourcing instructions as evidence of
# what a venture actually needs. These phrases describe the sourcing process,
# not the venture's business requirement.
SELF_REFERENTIAL_PHRASES=(
    "acquire real external evidence for missing procurement fields",
    "do not fabricate vendor",
    "do not fabricate price",
    "do not fabricate payment destination",
    "missing procurement fields",
    "official vendor evidence required",
    "checkout or invoice required",
    "provider comparison",
    "vendor selection",
    "procurement sourcing",
    "sourcing request",
    "payment destination",
    "evidence count",
)

TRUSTED_CONTEXT_ROOTS=(
    "profit_first_candidates","canonical_research_outputs","reports",
    "live_validation","venture_launch","ventures","generated_products",
    "specialist_evidence",
)

def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")

def save_json(path: Path,data: Any) -> None:
    import os,tempfile
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

def clean(s: Any) -> str:
    return " ".join(str(s or "").replace("_"," ").split()).strip()

def informative_tokens(s: str) -> list[str]:
    vals=re.findall(r"[a-z0-9][a-z0-9.+/-]{2,}",clean(s).lower())
    out=[]
    for x in vals:
        if x in GENERIC:
            continue
        if x not in out:
            out.append(x)
    return out

def generic_item(item: str,category: str) -> bool:
    i=clean(item).lower()
    c=clean(category).lower()
    if not i:
        return True
    exact={
        c,
        f"{c} requirement",
        f"{c} requirements",
        "software api requirement",
        "software api",
        "domain requirement",
        "hosting requirement",
        "general procurement",
        "marketplace software opportunity",
    }
    if i in exact:
        return True
    return len(informative_tokens(i)) < 2

def _walk(obj: Any,depth: int=0):
    if depth>7:
        return
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            yield from _walk(v,depth+1)
    elif isinstance(obj,list):
        for v in obj:
            yield from _walk(v,depth+1)

def _read_records(path: Path):
    try:
        text=path.read_text(errors="ignore")
    except Exception:
        return
    if path.suffix.lower()==".jsonl":
        for line in text.splitlines():
            try:o=json.loads(line)
            except Exception:continue
            yield from _walk(o)
    else:
        try:o=json.loads(text)
        except Exception:return
        yield from _walk(o)

def _is_procurement_internal_path(path: Path|str) -> bool:
    q=str(path).replace("\\","/").lower()
    return "/procurement/" in q or q.endswith("/procurement")

def _self_referential_text(text: str) -> bool:
    q=clean(text).lower()
    if not q:
        return False
    return any(x in q for x in SELF_REFERENTIAL_PHRASES)

def _trusted_context_path(path: Path|str) -> bool:
    if _is_procurement_internal_path(path):
        return False
    q=str(path).replace("\\","/").lower()
    return any(f"/{name.lower()}/" in q for name in TRUSTED_CONTEXT_ROOTS)

def _source_path(value: Any) -> Path|None:
    s=str(value or "")
    if not s:
        return None
    # V66.04 can store JSONL sources as "/path/file.jsonl:123".
    m=re.match(r"^(.*\.(?:json|jsonl))(?::\d+)?$",s,re.I)
    raw=m.group(1) if m else s
    p=Path(raw).expanduser()
    return p if p.exists() and p.is_file() else None

def _candidate_files(sr: dict[str,Any]) -> list[Path]:
    out=[]
    src=_source_path(sr.get("source_artifact"))
    if src and _trusted_context_path(src):
        out.append(src)

    vid=clean(sr.get("venture_id"))
    roots=[]
    for base in (RT,LOCAL_RT):
        for name in ROOT_NAMES:
            p=base/name
            if p.exists():
                roots.append(p)

    found=[]
    for root in roots:
        try:
            files=list(root.rglob("*.json"))+list(root.rglob("*.jsonl"))
        except Exception:
            continue
        for p in files:
            try:
                if p.stat().st_size>2_000_000:
                    continue
                score=2 if vid and vid.lower() in p.name.lower() else 0
                if score==0 and vid:
                    # Bounded content probe.
                    sample=p.read_text(errors="ignore")[:150000]
                    if vid in sample:
                        score=1
                if score:
                    found.append((score,p.stat().st_mtime,p))
            except Exception:
                continue

    found.sort(key=lambda x:(-x[0],-x[1]))
    for _,_,p in found[:80]:
        if p not in out:
            out.append(p)
    return out[:100]

def _context_strings(sr: dict[str,Any]) -> list[dict[str,Any]]:
    vid=clean(sr.get("venture_id"))
    rows=[]
    seen=set()

    for p in _candidate_files(sr):
        if not _trusted_context_path(p):
            continue
        for d in _read_records(p):
            dvid=clean(
                d.get("venture_id") or d.get("candidate_id")
                or d.get("project_id") or d.get("orchestration_id")
            )
            if vid and dvid and dvid!=vid:
                continue

            for k in CONTEXT_KEYS:
                v=d.get(k)
                if not isinstance(v,str):
                    continue
                txt=clean(v)
                if len(txt)<6 or len(txt)>500:
                    continue
                if _self_referential_text(txt):
                    continue
                key=(k,txt.lower())
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "field":k,
                    "text":txt,
                    "source":str(p),
                    "informative_tokens":informative_tokens(txt),
                })

    return rows

def _score_context(row: dict[str,Any],category: str) -> int:
    field=str(row.get("field") or "")
    text=str(row.get("text") or "")
    toks=row.get("informative_tokens") or []
    score=len(toks)*2

    high={
        "required_capability","capability_gap","required_resource",
        "required_service","integration_required","use_case","need",
        "requirement","objective","problem",
    }
    if field in high:
        score+=8
    elif field in {"product","service","offer","goal"}:
        score+=5
    elif field in {"title","name","business_model"}:
        score+=2

    q=text.lower()
    category_terms={
        "software_api":("api","integration","data","automation","software"),
        "domain":("domain","website","brand","site"),
        "hosting":("hosting","deploy","server","website","cloud"),
        "inventory_product":("inventory","supplier","wholesale","product"),
        "contractor_service":("contractor","service","labor","freelance"),
        "materials_equipment":("material","equipment","rental","machine","tool"),
        "advertising":("advertising","campaign","traffic","lead","marketing"),
    }.get(category,())
    score+=sum(3 for x in category_terms if x in q)
    return score

def specify(sr: dict[str,Any]) -> dict[str,Any]:
    item=clean(sr.get("item"))
    category=clean(sr.get("category")).replace(" ","_")
    vendor=clean(sr.get("known_vendor"))

    if not generic_item(item,category) and not _self_referential_text(item):
        result={
            "version":VERSION,
            "venture_id":sr.get("venture_id"),
            "category":category,
            "original_item":item,
            "specific_item":item,
            "requirement_specific":True,
            "source":"existing_explicit_requirement",
            "context_evidence":[],
            "fabricated":False,
        }
        append_jsonl(AUDIT,result)
        save_json(LATEST,result)
        return result

    rows=_context_strings(sr)
    scored=sorted(
        (( _score_context(r,category),r) for r in rows),
        key=lambda x:-x[0],
    )

    chosen=None
    for score,row in scored:
        if score<10:
            continue
        if len(row.get("informative_tokens") or [])<2:
            continue
        if not _trusted_context_path(row.get("source") or ""):
            continue
        if _self_referential_text(row.get("text") or ""):
            continue
        chosen={**row,"score":score}
        break

    if chosen:
        specific=chosen["text"]
        # Keep an explicit vendor in the specification only when one already
        # exists in the source data; never manufacture one here.
        if vendor and vendor.lower() not in specific.lower():
            specific=f"{specific} using {vendor}"
        result={
            "version":VERSION,
            "venture_id":sr.get("venture_id"),
            "category":category,
            "original_item":item,
            "specific_item":specific,
            "requirement_specific":True,
            "source":"trusted_venture_artifact_context",
            "context_evidence":[chosen],
            "provenance_verified":True,
            "self_reference_contamination":False,
            "fabricated":False,
        }
    else:
        result={
            "version":VERSION,
            "venture_id":sr.get("venture_id"),
            "category":category,
            "original_item":item,
            "specific_item":None,
            "requirement_specific":False,
            "source":"insufficient_explicit_venture_context",
            "context_evidence":rows[:10],
            "provenance_verified":False,
            "self_reference_contamination":False,
            "missing":["concrete procurement purpose or capability requirement from a trusted venture artifact"],
            "fabricated":False,
        }

    append_jsonl(AUDIT,result)
    save_json(LATEST,result)
    return result
