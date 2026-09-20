#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

from pathlib import Path
from collections import Counter
import hashlib
import json
import subprocess
import time

ROOT=Path.home()/"companyos"
IN=ROOT/"audit/COMPANYOS_V68_1_PRECISE_DUPLICATE_AUDIT.json"
OUT_JSON=ROOT/"audit/COMPANYOS_V68_2_ROLE_RESOLUTION.json"
OUT_MD=ROOT/"audit/COMPANYOS_V68_2_ROLE_RESOLUTION.md"

def git(*args):
    return subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()

def sha(rel):
    h=hashlib.sha256()
    with (ROOT/rel).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def tree_signature(base_rel):
    base=ROOT/base_rel
    if not base.exists() or not base.is_dir():
        return {"present":False}
    rows=[]
    for p in sorted(x for x in base.rglob("*") if x.is_file()):
        rel=p.relative_to(base).as_posix()
        # Ignore runtime/progress churn when comparing duplicated workspace roots.
        if "/companyos_progress/" in f"/{rel}/" or rel.startswith("companyos_progress/"):
            continue
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        rows.append((rel,h,p.stat().st_size))
    digest=hashlib.sha256(
        "\n".join(f"{r}|{h}|{s}" for r,h,s in rows).encode()
    ).hexdigest()
    return {
        "present":True,
        "file_count":len(rows),
        "bytes":sum(s for _,_,s in rows),
        "tree_sha256":digest,
    }

d=json.loads(IN.read_text())
groups=d.get("groups") or []

resolved=[]
future_candidates=[]
decision_counts=Counter()

for g in groups:
    files=list(g.get("files") or [])
    kind=g.get("kind")
    ev=g.get("evidence") or {}
    roles=g.get("roles") or {}

    rec={
        "kind":kind,
        "files":files,
        "decision":"manual_review",
        "keeper":None,
        "future_retirement_candidates":[],
        "reason":"",
    }

    # Semantic-equivalent code is not safe to dedupe based on AST similarity alone.
    if kind=="semantic":
        rec["decision"]="KEEP_PENDING_BEHAVIOR_REVIEW"
        rec["reason"]="AST-equivalent files may serve different subsystem contracts or side effects."
        resolved.append(rec); decision_counts[rec["decision"]]+=1
        continue

    # Generated-product archived snapshots: exact content + one live/current copy.
    archive_files=[f for f in files if f.startswith("generated_products/_archive/")]
    current_generated=[
        f for f in files
        if f.startswith("generated_products/") and not f.startswith("generated_products/_archive/")
    ]
    if archive_files and len(current_generated)==1:
        keeper=current_generated[0]
        candidates=[]
        for f in archive_files:
            e=ev.get(f,{})
            if not e.get("runtime_protected") and not e.get("source_imports") and not e.get("shell_entrypoints"):
                if sha(f)==sha(keeper):
                    candidates.append(f)
        rec["decision"]="ARCHIVE_HISTORY_EXACT_COPIES"
        rec["keeper"]=keeper
        rec["future_retirement_candidates"]=candidates
        rec["reason"]="Archived generated-product snapshots contain byte-identical test copies; current product copy is retained."
        for f in candidates:
            future_candidates.append({
                "path":f,
                "keeper":keeper,
                "class":"archive_history_exact_copy",
                "sha256":sha(f),
            })
        resolved.append(rec); decision_counts[rec["decision"]]+=1
        continue

    # Versioned/generated product tests belong to different product packages.
    if files and all(f.startswith("generated_products_v7/") for f in files):
        rec["decision"]="KEEP_PRODUCT_LOCAL_COPIES"
        rec["reason"]="Identical test source is intentionally packaged independently with different generated products."
        resolved.append(rec); decision_counts[rec["decision"]]+=1
        continue

    # Release artifact vs workspace current/version copies have different lifecycle roles.
    if any(f.startswith("releases/") for f in files) and any(f.startswith("workspace/") for f in files):
        rec["decision"]="KEEP_RELEASE_AND_WORKSPACE_ROLES"
        rec["reason"]="Release artifact, current prototype, and version snapshots are separate lifecycle roles even when byte-identical."
        resolved.append(rec); decision_counts[rec["decision"]]+=1
        continue

    # Marketplace package source vs installed plugin is an intentional two-copy lifecycle.
    role_set=set(roles.values())
    if {"marketplace_source_package","installed_plugin_copy"}.issubset(role_set):
        rec["decision"]="KEEP_MARKETPLACE_AND_INSTALLED_PLUGIN_ROLES"
        rec["reason"]="Marketplace package source and installed plugin copy are distinct deployment roles."
        resolved.append(rec); decision_counts[rec["decision"]]+=1
        continue

    # CompanyOS module vs script entrypoint: keep both roles.
    if "script_entrypoint" in role_set and "companyos_module" in role_set:
        rec["decision"]="KEEP_MODULE_AND_SCRIPT_ENTRYPOINT_ROLES"
        rec["reason"]="Importable module and executable/operational script are distinct roles."
        resolved.append(rec); decision_counts[rec["decision"]]+=1
        continue

    # Root-level shadow of an actively-used CompanyOS module. This is the only
    # non-archive pattern we allow as a future surgical candidate.
    companyos_members=[f for f in files if f.startswith("companyos/")]
    root_members=[f for f in files if "/" not in f]
    if len(companyos_members)==1 and len(root_members)==1:
        keeper=companyos_members[0]
        shadow=root_members[0]
        ke=ev.get(keeper,{})
        se=ev.get(shadow,{})
        keeper_active=bool(ke.get("runtime_protected") or ke.get("source_imports") or ke.get("shell_entrypoints"))
        shadow_dormant=not (
            se.get("runtime_protected") or se.get("source_imports") or
            se.get("shell_entrypoints") or se.get("test_references")
        )
        if keeper_active and shadow_dormant and sha(keeper)==sha(shadow):
            rec["decision"]="ROOT_SHADOW_EXACT_COPY_CANDIDATE"
            rec["keeper"]=keeper
            rec["future_retirement_candidates"]=[shadow]
            rec["reason"]="Root-level byte-identical shadow is dormant while package implementation has structured active callers."
            future_candidates.append({
                "path":shadow,
                "keeper":keeper,
                "class":"root_shadow_exact_copy",
                "sha256":sha(shadow),
            })
            resolved.append(rec); decision_counts[rec["decision"]]+=1
            continue

    # Duplicate subsystem utility modules with no clear active owner stay put.
    if files and all(f.startswith("companyos/") for f in files):
        active=[
            f for f in files
            if (ev.get(f,{ }).get("runtime_protected")
                or ev.get(f,{ }).get("source_imports")
                or ev.get(f,{ }).get("shell_entrypoints"))
        ]
        if not active:
            rec["decision"]="KEEP_UNRESOLVED_DORMANT_SUBSYSTEM_COPIES"
            rec["reason"]="No active caller establishes a canonical owner; deletion would be speculative."
        else:
            rec["decision"]="KEEP_ACTIVE_SUBSYSTEM_COPIES"
            rec["reason"]="One or more subsystem copies have structured active evidence."
        resolved.append(rec); decision_counts[rec["decision"]]+=1
        continue

    # Operational check bundles/scripts remain distinct unless a later audit proves one obsolete.
    if any("full_system_check" in f for f in files):
        rec["decision"]="KEEP_OPERATIONAL_CHECK_COPIES"
        rec["reason"]="Operational check bundle and standalone script may be invoked independently."
        resolved.append(rec); decision_counts[rec["decision"]]+=1
        continue

    rec["decision"]="KEEP_UNTIL_ROLE_PROVEN"
    rec["reason"]="No deterministic safe canonicalization rule matched."
    resolved.append(rec); decision_counts[rec["decision"]]+=1

# Case-variant workspace audit. This is audit-only and intentionally not a deletion candidate.
case_variant={}
upper="workspace/Local_Contractor_Bid_Organizer"
lower="workspace/local_contractor_bid_organizer"
u=tree_signature(upper)
l=tree_signature(lower)
case_variant={
    "upper_path":upper,
    "lower_path":lower,
    "upper":u,
    "lower":l,
    "equivalent_excluding_progress":bool(
        u.get("present") and l.get("present") and u.get("tree_sha256")==l.get("tree_sha256")
    ),
    "action":"manual_workspace_identity_review",
}

report={
    "schema":"companyos.v68_2.role_resolution.v1",
    "generated_at_unix":time.time(),
    "branch":git("branch","--show-current"),
    "head_sha":git("rev-parse","HEAD"),
    "mode":"AUDIT_ONLY_NO_FILE_MUTATION",
    "input_groups":len(groups),
    "decision_counts":dict(sorted(decision_counts.items())),
    "resolved_groups":resolved,
    "future_surgical_candidates":future_candidates,
    "future_surgical_candidate_count":len(future_candidates),
    "case_variant_workspace_audit":case_variant,
    "deletion_performed":False,
    "move_performed":False,
    "financial_limits_changed":False,
    "next_step":{
        "name":"V68.3 surgical exact-copy retirement",
        "scope":"future_surgical_candidates only",
        "requirements":[
            "remote recovery branch",
            "reverify byte equality before removal",
            "reverify keeper exists",
            "reverify candidate has zero structured active/test/entrypoint evidence",
            "full pytest",
            "runtime health",
            "launch readiness",
            "automatic rollback on failure",
        ],
    },
}

OUT_JSON.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")

lines=[
    "# CompanyOS V68.2 Canonical Role Resolution",
    "",
    "No files were moved or deleted.",
    "",
    f"- Duplicate groups reviewed: **{len(groups)}**",
    f"- Future surgical candidates: **{len(future_candidates)}**",
    f"- Case-variant workspace equivalent (excluding progress): **{case_variant['equivalent_excluding_progress']}**",
    "",
    "## Decisions",
]
for k,v in sorted(report["decision_counts"].items()):
    lines.append(f"- `{k}`: {v}")
lines += [
    "",
    "## Next step",
    "",
    "V68.3 may remove only the explicitly listed byte-identical dormant candidates after revalidation and creation of a remote recovery branch.",
]
OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")

print(json.dumps({
    "status":"PASS",
    "groups_reviewed":len(groups),
    "future_surgical_candidate_count":len(future_candidates),
    "decision_counts":report["decision_counts"],
    "case_variant_workspace_equivalent":case_variant["equivalent_excluding_progress"],
    "future_candidates":[x["path"] for x in future_candidates],
},indent=2,sort_keys=True))
