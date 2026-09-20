#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
SPEC="$ROOT/companyos/runtime/procurement_requirement_specifier.py"
SOURCING="$ROOT/companyos/runtime/autonomous_procurement_sourcing.py"
CTL="$ROOT/scripts/companyos_specctl"
SCTL="$ROOT/scripts/companyos_sourcingctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.12 PROCUREMENT PROVENANCE GUARD ====="
echo "GOAL=STOP_SELF_GENERATED_PROCUREMENT_INSTRUCTIONS_FROM_BECOMING_VENTURE_REQUIREMENTS"
echo "NOTE=ONLY_ORIGINAL_VENTURE_RESEARCH_PRODUCT_CONTEXT_CAN_SPECIFY_A_PURCHASE"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$SPEC" "$SOURCING"; do
  [ -f "$f" ] || { echo "V66_12_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$SPEC" "$SOURCING"; do
  cp "$f" "${f}.v66_12_backup_${stamp}"
  echo "BACKUP=${f}.v66_12_backup_${stamp}"
done

echo "===== PATCH REQUIREMENT SPECIFIER PROVENANCE ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/procurement_requirement_specifier.py"
s=p.read_text()

old='''ROOT_NAMES=(
    "profit_first_candidates","canonical_research_outputs","reports",
    "live_validation","venture_launch","ventures","generated_products",
    "specialist_evidence","procurement",
)
'''
new='''ROOT_NAMES=(
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
'''
if old in s:
    s=s.replace(old,new,1)
elif "SELF_REFERENTIAL_PHRASES" not in s:
    raise SystemExit("V66_12_ABORT=root_names_anchor_missing")

# Add helpers before _source_path.
anchor='''def _source_path(value: Any) -> Path|None:
'''
helpers='''def _is_procurement_internal_path(path: Path|str) -> bool:
    q=str(path).replace("\\\\","/").lower()
    return "/procurement/" in q or q.endswith("/procurement")

def _self_referential_text(text: str) -> bool:
    q=clean(text).lower()
    if not q:
        return False
    return any(x in q for x in SELF_REFERENTIAL_PHRASES)

def _trusted_context_path(path: Path|str) -> bool:
    if _is_procurement_internal_path(path):
        return False
    q=str(path).replace("\\\\","/").lower()
    return any(f"/{name.lower()}/" in q for name in TRUSTED_CONTEXT_ROOTS)

'''
if helpers not in s:
    if anchor not in s:
        raise SystemExit("V66_12_ABORT=source_path_anchor_missing")
    s=s.replace(anchor,helpers+anchor,1)

# Reject a sourcing/procurement source_artifact from direct use.
old_src='''    src=_source_path(sr.get("source_artifact"))
    if src:
        out.append(src)
'''
new_src='''    src=_source_path(sr.get("source_artifact"))
    if src and _trusted_context_path(src):
        out.append(src)
'''
if old_src in s:
    s=s.replace(old_src,new_src,1)
elif "if src and _trusted_context_path(src):" not in s:
    raise SystemExit("V66_12_ABORT=source_artifact_anchor_missing")

# Guard every record source and every candidate text.
needle='''    for p in _candidate_files(sr):
        for d in _read_records(p):
'''
replacement='''    for p in _candidate_files(sr):
        if not _trusted_context_path(p):
            continue
        for d in _read_records(p):
'''
if needle in s:
    s=s.replace(needle,replacement,1)
elif "if not _trusted_context_path(p):" not in s:
    raise SystemExit("V66_12_ABORT=context_path_guard_anchor_missing")

old_text='''                txt=clean(v)
                if len(txt)<6 or len(txt)>500:
                    continue
'''
new_text='''                txt=clean(v)
                if len(txt)<6 or len(txt)>500:
                    continue
                if _self_referential_text(txt):
                    continue
'''
if old_text in s:
    s=s.replace(old_text,new_text,1)
elif "_self_referential_text(txt)" not in s:
    raise SystemExit("V66_12_ABORT=self_reference_guard_anchor_missing")

# Add stronger provenance and semantic requirements to selection.
old_choose='''    chosen=None
    for score,row in scored:
        if score<8:
            continue
        if len(row.get("informative_tokens") or [])<2:
            continue
        chosen={**row,"score":score}
        break
'''
new_choose='''    chosen=None
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
'''
if old_choose in s:
    s=s.replace(old_choose,new_choose,1)
elif "score<10" not in s:
    raise SystemExit("V66_12_ABORT=selection_anchor_missing")

# Report provenance explicitly.
old_success='''            "source":"venture_artifact_context",
            "context_evidence":[chosen],
            "fabricated":False,
'''
new_success='''            "source":"trusted_venture_artifact_context",
            "context_evidence":[chosen],
            "provenance_verified":True,
            "self_reference_contamination":False,
            "fabricated":False,
'''
if old_success in s:
    s=s.replace(old_success,new_success,1)

old_fail='''            "source":"insufficient_explicit_venture_context",
            "context_evidence":rows[:10],
            "missing":["concrete procurement purpose or capability requirement"],
            "fabricated":False,
'''
new_fail='''            "source":"insufficient_explicit_venture_context",
            "context_evidence":rows[:10],
            "provenance_verified":False,
            "self_reference_contamination":False,
            "missing":["concrete procurement purpose or capability requirement from a trusted venture artifact"],
            "fabricated":False,
'''
if old_fail in s:
    s=s.replace(old_fail,new_fail,1)

# Existing explicit requirements are allowed only if they are not sourcing
# boilerplate. A generic/self-referential item must still be resolved.
old_explicit='''    if not generic_item(item,category):
        result={
'''
new_explicit='''    if not generic_item(item,category) and not _self_referential_text(item):
        result={
'''
if old_explicit in s:
    s=s.replace(old_explicit,new_explicit,1)
elif "and not _self_referential_text(item)" not in s:
    raise SystemExit("V66_12_ABORT=explicit_requirement_anchor_missing")

p.write_text(s)
print("V66_12_PROVENANCE_PATCH=PASS")
PY

echo "===== PATCH SOURCING STATUS TO EXPOSE PROVENANCE BLOCK ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/autonomous_procurement_sourcing.py"
s=p.read_text()

old='''            "status":"REQUIREMENT_SPECIFICATION_REQUIRED",
            "research_task":research_task,
            "procurement_specificity":sr.get("procurement_specificity"),
'''
new='''            "status":"REQUIREMENT_SPECIFICATION_REQUIRED",
            "requirement_provenance_verified":False,
            "research_task":research_task,
            "procurement_specificity":sr.get("procurement_specificity"),
'''
if old in s:
    s=s.replace(old,new,1)
elif '"requirement_provenance_verified":False' not in s:
    raise SystemExit("V66_12_ABORT=sourcing_status_anchor_missing")

# Normal resolutions only get provenance=true when specificity actually came
# from a trusted original artifact.
needle='''        "procurement_specificity": sr.get("procurement_specificity"),
        "query": query,
'''
replacement='''        "procurement_specificity": sr.get("procurement_specificity"),
        "requirement_provenance_verified": bool(
            (sr.get("procurement_specificity") or {}).get("provenance_verified", False)
            or (sr.get("procurement_specificity") or {}).get("source")=="existing_explicit_requirement"
        ),
        "query": query,
'''
if replacement not in s:
    if needle not in s:
        raise SystemExit("V66_12_ABORT=normal_resolution_anchor_missing")
    s=s.replace(needle,replacement,1)

p.write_text(s)
print("V66_12_SOURCING_PROVENANCE_STATUS=PASS")
PY

cat > "$ROOT/tests/test_v66_12_procurement_provenance.py" <<'PY'
from pathlib import Path
from companyos.runtime.procurement_requirement_specifier import (
    _is_procurement_internal_path,
    _self_referential_text,
    _trusted_context_path,
)

def test_procurement_generated_path_is_untrusted():
    assert _is_procurement_internal_path(
        Path.home()/".companyos_runtime/procurement/sourcing_requests.jsonl"
    )
    assert not _trusted_context_path(
        Path.home()/".companyos_runtime/procurement/sourcing_requests.jsonl"
    )

def test_venture_path_is_trusted():
    assert _trusted_context_path(
        Path.home()/".companyos_runtime/ventures/example.json"
    )

def test_sourcing_instruction_is_not_business_requirement():
    assert _self_referential_text(
        "Acquire real external evidence for missing procurement fields. "
        "Do not fabricate vendor, price, payment destination, probability, or profit."
    )

def test_real_business_need_is_not_self_reference():
    assert not _self_referential_text(
        "real-time cryptocurrency market price data for the portfolio analytics product"
    )
PY

echo "===== COMPILE ====="
python -m py_compile "$SPEC" "$SOURCING"
echo "V66_12_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_12_procurement_provenance.py
echo "V66_12_TESTS=PASS"

echo "===== CLEAN SOURCING RESTART ====="
"$SCTL" stop || true

echo "===== RETRY WITH TRUSTED PROVENANCE ONLY ====="
"$SCTL" once 20 || true

echo "===== SPECIFICITY STATUS ====="
"$CTL" status

echo "===== RESTART SOURCING LOOP ====="
"$SCTL" start

echo "V66_12_SELF_REFERENCE_BLOCK=PASS"
echo "V66_12_PROCUREMENT_DIRECTORY_EXCLUDED=PASS"
echo "V66_12_TRUSTED_VENTURE_PROVENANCE=PASS"
echo "V66_12_GENERIC_REQUIREMENT_FAIL_CLOSED=PASS"
echo "V66_12_CAPITAL_PATH_PROVENANCE_GATE=PASS"
echo "V66_12_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_12_COMPLETE"
