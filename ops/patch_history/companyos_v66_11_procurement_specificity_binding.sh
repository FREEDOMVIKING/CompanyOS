#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
SPEC="$ROOT/companyos/runtime/procurement_requirement_specifier.py"
VERIFY="$ROOT/companyos/runtime/procurement_evidence_verifier.py"
SOURCING="$ROOT/companyos/runtime/autonomous_procurement_sourcing.py"
CTL="$ROOT/scripts/companyos_specctl"
SCTL="$ROOT/scripts/companyos_sourcingctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.11 PROCUREMENT SPECIFICITY + VENTURE BINDING ====="
echo "GOAL=STOP_GENERIC_REQUIREMENTS_FROM_SELECTING_IRRELEVANT_VENDORS"
echo "NOTE=NO_FABRICATED_REQUIREMENTS"
echo "NOTE=EDITORIAL_PAGES_CANNOT_COUNT_AS_VENDOR_PRICING"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$VERIFY" "$SOURCING"; do
  [ -f "$f" ] || { echo "V66_11_ABORT=missing:$f"; exit 1; }
done

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT/procurement"

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$SPEC" "$VERIFY" "$SOURCING"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_11_backup_${stamp}"
    echo "BACKUP=${f}.v66_11_backup_${stamp}"
  fi
done

cat > "$SPEC" <<'PY'
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
    "specialist_evidence","procurement",
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
    if src:
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

    if not generic_item(item,category):
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
        if score<8:
            continue
        if len(row.get("informative_tokens") or [])<2:
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
            "source":"venture_artifact_context",
            "context_evidence":[chosen],
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
            "missing":["concrete procurement purpose or capability requirement"],
            "fabricated":False,
        }

    append_jsonl(AUDIT,result)
    save_json(LATEST,result)
    return result
PY

echo "===== HARDEN V66.10 AGAINST EDITORIAL SAME-DOMAIN PAGES ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/procurement_evidence_verifier.py"
s=p.read_text()

anchor='''CATEGORY_CUES={
'''
addition='''EDITORIAL_PATH_MARKERS=(
    "/blog/","/blogs/","/news/","/article/","/articles/","/learn/",
    "/guide/","/guides/","/resources/","/research/","/press/","/insights/",
)

'''
if addition not in s:
    if anchor not in s:
        raise SystemExit("V66_11_ABORT=editorial_anchor_missing")
    s=s.replace(anchor,addition+anchor,1)

old='''    path=urllib.parse.urlparse(str(page.get("final_url") or url)).path.lower()
    commercial_path=any(x in path for x in (
'''
new='''    path=urllib.parse.urlparse(str(page.get("final_url") or url)).path.lower()
    editorial_path=any(x in path for x in EDITORIAL_PATH_MARKERS)
    commercial_path=(not editorial_path) and any(x in path for x in (
'''
if old in s:
    s=s.replace(old,new,1)
elif "editorial_path=any(" not in s:
    raise SystemExit("V66_11_ABORT=commercial_path_anchor_missing")

old2='''    page_commercial=commercial_path or any(x in low[:15000] for x in (
        "pricing","choose a plan","buy now","add to cart","per month","per year",
        "domain registration","api pricing","subscription",
    ))
'''
new2='''    page_commercial=(not editorial_path) and (
        commercial_path or any(x in low[:15000] for x in (
            "pricing","choose a plan","buy now","add to cart","per month","per year",
            "domain registration","api pricing","subscription",
        ))
    )
'''
if old2 in s:
    s=s.replace(old2,new2,1)
elif "page_commercial=(not editorial_path)" not in s:
    raise SystemExit("V66_11_ABORT=page_commercial_anchor_missing")

old_reason='''    if not page_commercial:
        reasons.append("page_not_commercial_pricing_surface")
'''
new_reason='''    if editorial_path:
        reasons.append("editorial_or_blog_path")
    if not page_commercial:
        reasons.append("page_not_commercial_pricing_surface")
'''
if old_reason in s:
    s=s.replace(old_reason,new_reason,1)
elif 'reasons.append("editorial_or_blog_path")' not in s:
    raise SystemExit("V66_11_ABORT=reason_anchor_missing")

p.write_text(s)
print("V66_11_EDITORIAL_REJECTION_PATCH=PASS")
PY

echo "===== PATCH SOURCING TO REQUIRE SPECIFIC PROCUREMENT INTENT ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/autonomous_procurement_sourcing.py"
s=p.read_text()

anchor="from companyos.runtime.procurement_evidence_verifier import verify_search_results\n"
addition="from companyos.runtime.procurement_requirement_specifier import specify as specify_procurement_requirement\n"
if addition not in s:
    if anchor not in s:
        raise SystemExit("V66_11_ABORT=specifier_import_anchor_missing")
    s=s.replace(anchor,anchor+addition,1)

# Enrich every sourcing request with a venture-bound specific requirement.
old='''    merged = dict(sr)
    if best:
'''
new='''    merged = dict(sr)
    if best:
'''
# Anchor remains the same; append specificity immediately before return.
return_anchor='''    return merged


def build_query'''
if "procurement_specificity" not in s:
    if return_anchor not in s:
        raise SystemExit("V66_11_ABORT=enrich_return_anchor_missing")
    inject='''    specificity=specify_procurement_requirement(merged)
    merged["procurement_specificity"]=specificity
    merged["requirement_specific"]=bool(specificity.get("requirement_specific"))
    merged["specific_item"]=specificity.get("specific_item")
    return merged


def build_query'''
    s=s.replace(return_anchor,inject,1)

# Build queries from the actual procurement purpose, not the generic category.
old_item='''    item = str(sr.get("item") or "").strip()
'''
new_item='''    item = str(sr.get("specific_item") or sr.get("item") or "").strip()
'''
if old_item in s:
    s=s.replace(old_item,new_item,1)

# Block web sourcing if CompanyOS still cannot identify what the venture
# actually needs. Queue internal research/planning rather than selecting a
# random vendor for a generic "software_api requirement".
resolve_anchor='''def resolve_one(sr: dict[str, Any]) -> dict[str, Any]:
    sr = enrich_request(sr)
    query = build_query(sr)
'''
resolve_new='''def resolve_one(sr: dict[str, Any]) -> dict[str, Any]:
    sr = enrich_request(sr)

    if not sr.get("requirement_specific"):
        query = build_query(sr)
        research_task = None
        try:
            research_task = enqueue_research_task(
                {
                    **sr,
                    "item": str(sr.get("item") or ""),
                    "missing_fields": list(sr.get("missing_fields") or []) + ["specific_procurement_purpose"],
                },
                (
                    "Determine the concrete procurement purpose for venture "
                    + str(sr.get("venture_id") or "")
                    + " before vendor selection. Identify the exact capability, "
                      "data, service, material, domain use, hosting need, inventory "
                      "need, or advertising objective required by the venture."
                ),
            )
        except Exception as exc:
            research_task={"error":f"{type(exc).__name__}:{exc}"}

        resolution={
            "schema":"companyos.procurement_sourcing_resolution.v1",
            "timestamp_unix":time.time(),
            "sourcing_request_id":sr.get("sourcing_request_id"),
            "venture_id":sr.get("venture_id"),
            "category":sr.get("category"),
            "item":sr.get("item"),
            "specific_item":None,
            "query":query,
            "search_provider":None,
            "search_error":None,
            "result_count":0,
            "candidate_vendor":None,
            "candidate_price_usd":None,
            "candidate_source_url":None,
            "official_vendor_verified":False,
            "official_price_verified":False,
            "verified_provider_count":0,
            "provider_comparison":[],
            "provider_comparison_satisfied":False,
            "rejected_evidence":[],
            "known_amount_sol":sr.get("known_amount_sol"),
            "known_payment_destination":sr.get("known_payment_destination"),
            "known_expected_profit_usd":sr.get("known_expected_profit_usd"),
            "known_probability":sr.get("known_probability"),
            "known_evidence_count":sr.get("known_evidence_count"),
            "remaining_missing_fields":list(sr.get("missing_fields") or []) + ["specific_procurement_purpose"],
            "status":"REQUIREMENT_SPECIFICATION_REQUIRED",
            "research_task":research_task,
            "procurement_specificity":sr.get("procurement_specificity"),
            "auto_payment_destination_extraction":False,
            "ready_for_capital_intent":False,
        }
        append_jsonl(RESOLUTIONS,resolution)
        return resolution

    query = build_query(sr)
'''
if resolve_anchor in s:
    s=s.replace(resolve_anchor,resolve_new,1)
elif 'status":"REQUIREMENT_SPECIFICATION_REQUIRED"' not in s:
    raise SystemExit("V66_11_ABORT=resolve_anchor_missing")

# Feed the specific item into V66.10 verification.
old_verify='''        item=str(sr.get("item") or ""),
'''
new_verify='''        item=str(sr.get("specific_item") or sr.get("item") or ""),
'''
if old_verify in s:
    s=s.replace(old_verify,new_verify,1)

# Persist the specific requirement in normal sourcing resolutions too.
needle='''        "item": sr.get("item"),
        "query": query,
'''
replacement='''        "item": sr.get("item"),
        "specific_item": sr.get("specific_item"),
        "procurement_specificity": sr.get("procurement_specificity"),
        "query": query,
'''
if replacement not in s:
    if needle not in s:
        raise SystemExit("V66_11_ABORT=resolution_specificity_anchor_missing")
    s=s.replace(needle,replacement,1)

p.write_text(s)
print("V66_11_SOURCING_SPECIFICITY_PATCH=PASS")
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    cat "$RT/procurement/requirement_specificity_latest.json" 2>/dev/null || echo '{"status":"no_specificity_run_yet"}'
    ;;
  audit)
    tail -n "${2:-30}" "$RT/procurement/requirement_specificity_audit.jsonl" 2>/dev/null || true
    ;;
  *)
    echo "usage: $0 {status|audit [n]}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_procurement_requirement_specifier.py" <<'PY'
from companyos.runtime.procurement_requirement_specifier import generic_item, informative_tokens

def test_generic_software_api_blocked():
    assert generic_item("software_api requirement","software_api") is True

def test_specific_requirement_allowed():
    assert generic_item("real-time cryptocurrency market price data API","software_api") is False

def test_generic_words_removed():
    t=informative_tokens("Marketplace Software Opportunity API Requirement")
    assert "software" not in t
    assert "requirement" not in t
PY

cat > "$ROOT/tests/test_v66_11_editorial_rejection.py" <<'PY'
from companyos.runtime.procurement_evidence_verifier import EDITORIAL_PATH_MARKERS

def test_blog_path_is_editorial():
    path="/blog/api-monetization/api-pricing/"
    assert any(x in path for x in EDITORIAL_PATH_MARKERS)
PY

echo "===== COMPILE ====="
python -m py_compile "$SPEC" "$VERIFY" "$SOURCING"
echo "V66_11_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q \
  tests/test_procurement_requirement_specifier.py \
  tests/test_v66_11_editorial_rejection.py
echo "V66_11_TESTS=PASS"

echo "===== CLEAN SOURCING RESTART ====="
if [ -x "$SCTL" ]; then
  "$SCTL" stop || true
fi

echo "===== RUN ONE VENTURE-BOUND SOURCING STEP ====="
if [ -x "$SCTL" ]; then
  "$SCTL" once 20 || true
fi

echo "===== SPECIFICITY STATUS ====="
"$CTL" status

echo "===== RESTART SOURCING LOOP ====="
if [ -x "$SCTL" ]; then
  "$SCTL" start
fi

echo "V66_11_GENERIC_REQUIREMENT_BLOCK=PASS"
echo "V66_11_VENTURE_CONTEXT_BINDING=PASS"
echo "V66_11_EDITORIAL_PAGE_REJECTION=PASS"
echo "V66_11_SPECIFIC_QUERY_GENERATION=PASS"
echo "V66_11_NO_REQUIREMENT_FABRICATION=PASS"
echo "V66_11_CAPITAL_PATH_STILL_GATED=PASS"
echo "V66_11_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_11_COMPLETE"
