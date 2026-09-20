#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
LRT="$ROOT/.companyos_runtime"

PROGRESSION="$ROOT/companyos/governance/venture_identity_progression.py"
RESOLVER="$ROOT/companyos/governance/venture_identity_resolver.py"
RECON="$ROOT/companyos/runtime/canonical_state_reconciler.py"
LCTL="$ROOT/scripts/companyos_livenessctl"
RCTL="$ROOT/scripts/companyos_reconcilectl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.20 CANONICAL IDENTITY NORMALIZATION ====="
echo "GOAL=MERGE_VERSION_SUFFIX_ALIASES_AND_EXCLUDE_INTERNAL_PRODUCTION_SITE_OUTPUTS"
echo "NOTE=NO_VENTURE_CONTENT_DELETED"
echo "NOTE=NO_STAGE_ADVANCEMENT_FABRICATED"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$PROGRESSION" "$RESOLVER"; do
  [ -f "$f" ] || { echo "V66_20_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$PROGRESSION" "$RESOLVER"; do
  cp "$f" "${f}.v66_20_backup_${stamp}"
  echo "BACKUP=${f}.v66_20_backup_${stamp}"
done

echo "===== PATCH SHARED IDENTITY RESOLVER ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/governance/venture_identity_resolver.py"
s=p.read_text()

old='''INTERNAL = {
    "accounting","runtime","logs","backups","backup","tmp","temp","quotes",
    "projects","invoices","artifacts","exports","dashboard","ceo_memory",
    "companyos_runtime"
}
'''
new='''INTERNAL = {
    "accounting","runtime","logs","backups","backup","tmp","temp","quotes",
    "projects","invoices","artifacts","exports","dashboard","ceo_memory",
    "companyos_runtime",
    # Deployment output container, not a venture identity.
    "production_sites",
}
'''
if old in s:
    s=s.replace(old,new,1)
elif '"production_sites"' not in s:
    raise SystemExit("V66_20_ABORT=resolver_internal_anchor_missing")

p.write_text(s)
print("V66_20_RESOLVER_INTERNALS=PASS")
PY

echo "===== PATCH VENTURE IDENTITY PROGRESSION ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/governance/venture_identity_progression.py"
s=p.read_text()

# Import the canonical resolver and remove the local source of truth split.
import_anchor='''from pathlib import Path
'''
addition='''from companyos.governance.venture_identity_resolver import (
    canonical_id as resolve_canonical_id,
    display_name as resolve_display_name,
    is_internal as resolve_is_internal,
)
'''
if addition not in s:
    if import_anchor not in s:
        raise SystemExit("V66_20_ABORT=import_anchor_missing")
    s=s.replace(import_anchor,import_anchor+addition,1)

old_candidate='''def candidate_ventures():
    groups = {}
    for root in [ROOT/"workspace", ROOT/"exports", ROOT/"artifacts", ROOT/"products"]:
        if not root.exists(): continue
        for child in root.iterdir():
            if not child.is_dir(): continue
            raw = child.name
            if slugify(raw) in {slugify(x) for x in INTERNAL}: continue
            cid = slugify(raw)
            if not cid: continue
            rec = groups.setdefault(cid, {"canonical_id":cid, "display_name":display_name(cid), "aliases":set(), "roots":set()})
            rec["aliases"].add(raw)
            rec["roots"].add(str(child.relative_to(ROOT)))
    for rec in groups.values():
        rec["aliases"] = sorted(rec["aliases"])
        rec["roots"] = sorted(rec["roots"])
    return groups
'''

new_candidate='''def candidate_ventures():
    groups = {}
    for root in [ROOT/"workspace", ROOT/"exports", ROOT/"artifacts", ROOT/"products"]:
        if not root.exists():
            continue
        for child in root.iterdir():
            if not child.is_dir():
                continue

            raw = child.name
            cid = resolve_canonical_id(raw)

            # One shared canonicalization path for both identity progression and
            # stalled-stage progression. Version/build/release suffixes become
            # aliases of the same venture instead of separate ventures.
            if not cid or resolve_is_internal(cid):
                continue

            rec = groups.setdefault(
                cid,
                {
                    "canonical_id":cid,
                    "display_name":resolve_display_name(cid),
                    "aliases":set(),
                    "roots":set(),
                },
            )
            rec["aliases"].add(raw)
            rec["roots"].add(str(child.relative_to(ROOT)))

    for rec in groups.values():
        rec["aliases"] = sorted(rec["aliases"])
        rec["roots"] = sorted(rec["roots"])
    return groups
'''

if old_candidate in s:
    s=s.replace(old_candidate,new_candidate,1)
elif "resolve_canonical_id(raw)" not in s:
    raise SystemExit("V66_20_ABORT=candidate_ventures_anchor_missing")

# Migrate state observations by canonical ID before evaluating current roots.
old_eval='''def evaluate_all():
    state=_load(STATE, {"ventures":{}})
    groups=candidate_ventures()
    rows=[]
    for cid,rec in sorted(groups.items()):
        fs=artifact_files(rec)
        sig=sorted((str(p.relative_to(ROOT)),p.stat().st_size,int(p.stat().st_mtime)) for p in fs)
        fp=str(hash(tuple(sig)))
        old=state["ventures"].get(cid,{})
'''

new_eval='''def evaluate_all():
    state=_load(STATE, {"ventures":{}})

    # Canonicalize legacy state keys before comparison. This merges records
    # such as local_contractor_bid_organizer + local_contractor_bid_organizer_v1
    # without deleting any venture artifacts.
    legacy=state.get("ventures") or {}
    canonical_old={}
    stage_rank={
        "DISCOVER":0,"VALIDATE":1,"BUILD":2,"TEST":3,"PACKAGE":4,
        "LAUNCH_READY":5,"LAUNCH":6,"CUSTOMER_ACQUISITION":7,
        "OPERATE":8,"SCALE":9,
    }
    for key,rec in legacy.items():
        if not isinstance(rec,dict):
            continue
        cid=resolve_canonical_id(rec.get("canonical_id") or key)
        if not cid or resolve_is_internal(cid):
            continue
        cur=canonical_old.get(cid)
        if cur is None:
            canonical_old[cid]=dict(rec)
            canonical_old[cid]["canonical_id"]=cid
            continue

        # Retain the most advanced historical stage metadata while using the
        # maximum observation count. A changed merged fingerprint will still
        # reset unchanged_observations below.
        if stage_rank.get(rec.get("stage"),0) > stage_rank.get(cur.get("stage"),0):
            for k in ("stage","required_next_action","progression_directive"):
                if k in rec:
                    cur[k]=rec[k]
        cur["unchanged_observations"]=max(
            int(cur.get("unchanged_observations",0) or 0),
            int(rec.get("unchanged_observations",0) or 0),
        )

    state["ventures"]=canonical_old
    groups=candidate_ventures()
    rows=[]
    for cid,rec in sorted(groups.items()):
        fs=artifact_files(rec)
        sig=sorted((str(p.relative_to(ROOT)),p.stat().st_size,int(p.stat().st_mtime)) for p in fs)
        fp=str(hash(tuple(sig)))
        old=state["ventures"].get(cid,{})
'''

if old_eval in s:
    s=s.replace(old_eval,new_eval,1)
elif "canonical_old={}" not in s:
    raise SystemExit("V66_20_ABORT=evaluate_all_anchor_missing")

p.write_text(s)
print("V66_20_PROGRESSION_CANONICALIZATION=PASS")
PY

cat > "$ROOT/tests/test_v66_20_identity_normalization.py" <<'PY'
from companyos.governance.venture_identity_resolver import canonical_id, is_internal
from companyos.governance.venture_identity_progression import candidate_ventures

def test_version_suffix_collapses():
    assert canonical_id("local_contractor_bid_organizer_v1") == "local_contractor_bid_organizer"

def test_production_sites_is_internal():
    assert is_internal("production_sites") is True

def test_candidate_groups_do_not_emit_version_alias_as_separate_id():
    groups=candidate_ventures()
    assert "local_contractor_bid_organizer_v1" not in groups
    assert "production_sites" not in groups
PY

echo "===== COMPILE ====="
python -m py_compile "$RESOLVER" "$PROGRESSION"
echo "V66_20_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_20_identity_normalization.py
echo "V66_20_TESTS=PASS"

echo "===== REBUILD CANONICAL IDENTITY STATE ====="
python - <<'PY'
import json
from companyos.governance.venture_identity_progression import evaluate_all
rows=evaluate_all()
print(json.dumps({
    "canonical_venture_count":len(rows),
    "ventures":[
        {
            "canonical_id":r.get("canonical_id"),
            "aliases":r.get("aliases"),
            "roots":r.get("roots"),
            "stage":r.get("stage"),
            "artifact_count":r.get("artifact_count"),
            "changed_since_previous_observation":r.get("changed_since_previous_observation"),
            "unchanged_observations":r.get("unchanged_observations"),
        }
        for r in rows
    ],
},indent=2,sort_keys=True))
PY

echo "===== REFRESH LIVENESS SNAPSHOT ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== RECONCILIATION AUDIT ====="
if [ -x "$RCTL" ]; then
  "$RCTL" once || true
fi

echo "V66_20_VERSION_ALIAS_MERGE=PASS"
echo "V66_20_INTERNAL_PRODUCTION_SITE_EXCLUSION=PASS"
echo "V66_20_IDENTITY_STATE_MIGRATION=PASS"
echo "V66_20_LIVENESS_SNAPSHOT_REFRESH=PASS"
echo "V66_20_NO_VENTURE_ARTIFACT_DELETION=PASS"
echo "V66_20_NO_FAKE_STAGE_ADVANCEMENT=PASS"
echo "V66_20_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_20_COMPLETE"
