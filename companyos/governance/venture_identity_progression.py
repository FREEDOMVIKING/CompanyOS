from __future__ import annotations
import json, re, time
from pathlib import Path

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

def artifact_files(rec):
    out=[]
    for rel in rec.get("roots", []):
        r=ROOT/rel
        if not r.exists(): continue
        out.extend([p for p in r.rglob("*") if p.is_file()])
    return out

def infer_stage(files):
    names=" ".join(str(p).lower() for p in files)

    explicit_order = [
        ("venture_stage_scale", "SCALE"),
        ("venture_stage_operate", "OPERATE"),
        ("venture_stage_customer_acquisition", "CUSTOMER_ACQUISITION"),
        ("venture_stage_launch", "LAUNCH"),
        ("venture_stage_launch_ready", "LAUNCH_READY"),
        ("venture_stage_package", "PACKAGE"),
        ("venture_stage_test", "TEST"),
        ("venture_stage_build", "BUILD"),
        ("venture_stage_validate", "VALIDATE"),
    ]
    for marker, stage in explicit_order:
        if marker in names:
            return stage

    if any(x in names for x in (
        "conversion_result", "customer_result", "lead_result",
        "outreach_result", "campaign_result",
    )):
        return "CUSTOMER_ACQUISITION"
    if "deployment_result" in names or "live_url" in names:
        return "LAUNCH"
    if any(p.suffix==".zip" for p in files) or "export_manifest" in names:
        return "LAUNCH_READY"
    if any(x in names for x in ("test_result","qa_result","acceptance_result")):
        return "TEST"
    if "validation_result" in names:
        return "VALIDATE"
    if files:
        return "BUILD"
    return "DISCOVER"

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
    groups=candidate_ventures()
    rows=[]
    for cid,rec in sorted(groups.items()):
        fs=artifact_files(rec)
        sig=sorted((str(p.relative_to(ROOT)),p.stat().st_size,int(p.stat().st_mtime)) for p in fs)
        fp=str(hash(tuple(sig)))
        old=state["ventures"].get(cid,{})
        unchanged=int(old.get("unchanged_observations",0))+1 if old.get("fingerprint")==fp else 0
        stage=infer_stage(fs)
        row={**rec,
             "stage":stage,
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
    rank={"DISCOVER":0,"VALIDATE":1,"BUILD":2,"TEST":3,"PACKAGE":4,"LAUNCH_READY":5,"LAUNCH":6,"CUSTOMER_ACQUISITION":7,"OPERATE":8,"SCALE":9}
    rows.sort(key=lambda r:(rank.get(r.get("stage"),0),r.get("unchanged_observations",0)),reverse=True)
    return rows[0]
