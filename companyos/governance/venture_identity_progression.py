from __future__ import annotations
import json
import json, re, time
from pathlib import Path
from companyos.governance.venture_identity_resolver import (
    canonical_id as resolve_canonical_id,
    display_name as resolve_display_name,
    is_internal as resolve_is_internal,
)

ROOT = Path.home() / "companyos"
STATE = ROOT / ".companyos_runtime" / "venture_identity_progression.json"
INTERNAL = {"accounting","runtime","logs","backups","backup","tmp","temp","quotes","projects","invoices","artifacts","exports","dashboard","ceo_memory","companyos_runtime"}

def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())
    return re.sub(r"_+", "_", s).strip("_")

def display_name(slug: str) -> str:
    return "_".join(x.capitalize() for x in slug.split("_") if x)

def _load(path, default):
    try: return json.loads(path.read_text())
    except Exception: return default

def _save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n")

def candidate_ventures():
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

def artifact_files(rec):
    out=[]
    for rel in rec.get("roots", []):
        r=ROOT/rel
        if not r.exists(): continue
        out.extend([p for p in r.rglob("*") if p.is_file()])
    return out

STAGE_RANK = {
    "DISCOVER":0,
    "VALIDATE":1,
    "BUILD":2,
    "TEST":3,
    "PACKAGE":4,
    "LAUNCH_READY":5,
    "LAUNCH":6,
    "CUSTOMER_ACQUISITION":7,
    "OPERATE":8,
    "SCALE":9,
}

def max_stage(*stages):
    valid=[str(x) for x in stages if str(x) in STAGE_RANK]
    if not valid:
        return "DISCOVER"
    return max(valid, key=lambda x: STAGE_RANK[x])

def infer_stage(files):
    names=" ".join(str(p).lower() for p in files)
    observed=[]

    explicit_markers=[
        ("venture_stage_scale","SCALE"),
        ("venture_stage_operate","OPERATE"),
        ("venture_stage_customer_acquisition","CUSTOMER_ACQUISITION"),
        ("venture_stage_launch_ready","LAUNCH_READY"),
        ("venture_stage_launch","LAUNCH"),
        ("venture_stage_package","PACKAGE"),
        ("venture_stage_test","TEST"),
        ("venture_stage_build","BUILD"),
        ("venture_stage_validate","VALIDATE"),
    ]
    for marker,stage in explicit_markers:
        if marker in names:
            observed.append(stage)

    if any(x in names for x in (
        "conversion_result","customer_result","lead_result",
        "outreach_result","campaign_result",
    )):
        observed.append("CUSTOMER_ACQUISITION")

    if any(x in names for x in (
        "deployment_result","real_deployment_result","live_url",
    )):
        observed.append("LAUNCH")

    if any(p.suffix.lower()==".zip" for p in files) or "export_manifest" in names:
        observed.append("LAUNCH_READY")

    if any(x in names for x in (
        "test_result","qa_result","acceptance_result",
    )):
        observed.append("TEST")

    if "validation_result" in names:
        observed.append("VALIDATE")

    if files:
        observed.append("BUILD")

    verified=verified_external_stage(files)
    if verified:
        observed.append(verified)
    return max_stage(*observed)

def _iter_json_objects(path):
    try:
        text=path.read_text(errors="ignore")
    except Exception:
        return
    if path.suffix.lower()==".jsonl":
        for line in text.splitlines():
            try:
                obj=json.loads(line)
            except Exception:
                continue
            if isinstance(obj,dict):
                yield obj
    elif path.suffix.lower()==".json":
        try:
            obj=json.loads(text)
        except Exception:
            return
        if isinstance(obj,dict):
            yield obj

def verified_external_stage(files):
    observed=[]

    for path in files:
        low_name=str(path).lower()
        likely=any(x in low_name for x in (
            "deployment_result",
            "real_deployment_result",
            "live_url",
            "customer_result",
            "conversion_result",
            "lead_result",
            "outreach_result",
            "campaign_result",
        ))
        if not likely or path.suffix.lower() not in {".json",".jsonl"}:
            continue

        for obj in _iter_json_objects(path):
            schema=str(obj.get("schema") or "").lower()
            connector=str(obj.get("connector") or "").lower()
            action=str(obj.get("action") or "").lower()
            status=str(obj.get("status") or "").lower()
            result=obj.get("result") if isinstance(obj.get("result"),dict) else {}

            ok=(
                obj.get("ok") is True
                or result.get("ok") is True
                or status in {"ok","success","succeeded","completed","executed"}
            )

            live_url=(
                obj.get("live_url")
                or result.get("live_url")
                or result.get("url")
            )
            deployment_id=(
                obj.get("deployment_id")
                or result.get("deployment_id")
            )

            real_deploy=(
                (
                    "real_deployment_result" in schema
                    or connector=="hosting"
                    or action=="deploy_production"
                    or "deployment_result" in low_name
                )
                and ok
                and bool(live_url or deployment_id)
            )
            if real_deploy:
                observed.append("LAUNCH")

            customer_signal=any(x in (schema+" "+low_name) for x in (
                "customer_result",
                "conversion_result",
                "lead_result",
                "outreach_result",
                "campaign_result",
            ))
            if customer_signal and ok:
                observed.append("CUSTOMER_ACQUISITION")

    return max_stage(*observed) if observed else None

def next_action(stage):
    return {
        "DISCOVER":"validate demand and customer problem before building",
        "VALIDATE":"build the smallest sellable product",
        "BUILD":"test the product against explicit acceptance criteria",
        "TEST":"package a release candidate",
        "PACKAGE":"prepare deployment and launch assets",
        "LAUNCH_READY":"perform authorized launch/deployment steps or prepare an operator-ready launch packet",
        "LAUNCH":"begin measurable customer acquisition",
        "CUSTOMER_ACQUISITION":"run measurable acquisition experiments, track conversion, fulfill customers, and collect feedback",
        "OPERATE":"improve retention, reliability, fulfillment, margin, and repeatability",
        "SCALE":"expand only from measured evidence",
    }.get(stage, "advance to the next measurable lifecycle milestone")

def evaluate_all():
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
        unchanged=int(old.get("unchanged_observations",0))+1 if old.get("fingerprint")==fp else 0
        verified_stage=verified_external_stage(fs)
        inferred_stage=infer_stage(fs)
        stage=max_stage(inferred_stage, verified_stage, old.get("stage"))
        row={**rec,
             "stage":stage,
             "inferred_stage":inferred_stage,
             "verified_external_stage":verified_stage,
             "stage_regression_blocked":(
                 old.get("stage") in STAGE_RANK
                 and STAGE_RANK.get(str(old.get("stage")),0)
                     > STAGE_RANK.get(inferred_stage,0)
             ),
             "artifact_count":len(fs),
             "fingerprint":fp,
             "changed_since_previous_observation":old.get("fingerprint") not in (None,fp),
             "unchanged_observations":unchanged,
             "duplicate_work_risk":unchanged>=3,
             "required_next_action":next_action(stage),
             "progression_directive":f"Continue canonical venture '{cid}'. Current stage: {stage}. Next meaningful action: {next_action(stage)}. Reuse existing artifacts and do not rebuild equivalent outputs unless a failed test or new requirement requires it.",
             "updated_at_unix":time.time()}
        state["ventures"][cid]=row
        rows.append(row)
    state["ventures"]={k:v for k,v in state["ventures"].items() if k in groups}
    _save(STATE,state)
    return rows

def highest_priority_stalled():
    rows=[r for r in evaluate_all() if r.get("duplicate_work_risk")]
    if not rows: return None
    rows.sort(
        key=lambda r:(
            STAGE_RANK.get(r.get("stage"),0),
            r.get("unchanged_observations",0),
        ),
        reverse=True,
    )
    return rows[0]
