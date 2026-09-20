#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import time

ROOT=Path.home()/"companyos"
BASE_REPORT=ROOT/"audit/COMPANYOS_V68_DUPLICATE_CURRENT_AUDIT.json"
CANONICAL=ROOT/"config/companyos_active_component_manifest.json"
OUT_JSON=ROOT/"audit/COMPANYOS_V68_1_PRECISE_DUPLICATE_AUDIT.json"
OUT_MD=ROOT/"audit/COMPANYOS_V68_1_PRECISE_DUPLICATE_AUDIT.md"

SOURCE_PREFIXES=(
    "companyos/",
    "scripts/",
    "agents/",
    "connectors/",
    "plugins/",
    "marketplace/",
    "modules/",
)
TEST_PREFIXES=("tests/","tests_",)
NON_RUNTIME_PREFIXES=(
    "audit/",
    "docs/",
    "ceo_memory/",
    "generated_products/",
    "generated_products_v",
    "local_marketplace/",
    "releases/",
    "backups/",
    "ops/patch_history/",
)
TEXT_EXT={".py",".sh",".json",".toml",".yaml",".yml",".md",".txt"}

def git(*args):
    return subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()

def tracked():
    return git("ls-files").splitlines()

def module_name(rel):
    if not rel.endswith(".py"):
        return None
    if rel.endswith("/__init__.py"):
        return rel[:-12].replace("/",".")
    return rel[:-3].replace("/",".")

def parse_imports(rel):
    p=ROOT/rel
    try:
        tree=ast.parse(p.read_text(errors="ignore"))
    except Exception:
        return set()
    out=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node,ast.ImportFrom) and node.module:
            out.add(node.module)
    return out

def shell_mentions(rel,target):
    try:
        text=(ROOT/rel).read_text(errors="ignore")
    except Exception:
        return False
    needles={target}
    mod=module_name(target)
    if mod:
        needles.update({f"-m {mod}", f"-m '{mod}'", f'-m "{mod}"'})
    return any(n in text for n in needles)

def sha256(rel):
    h=hashlib.sha256()
    with (ROOT/rel).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

files=tracked()
base=json.loads(BASE_REPORT.read_text())
manifest=json.loads(CANONICAL.read_text())

protected={
    rec["path"]
    for rec in (manifest.get("component_status") or {}).values()
    if isinstance(rec,dict) and rec.get("path")
}

# Supervisor-owned modules are runtime-protected.
try:
    from companyos.runtime.service_supervisor import ServiceSupervisor
    for spec in ServiceSupervisor.default_services():
        argv=list(spec.argv)
        if "-m" in argv:
            i=argv.index("-m")
            if i+1 < len(argv):
                rel=argv[i+1].replace(".","/")+".py"
                if (ROOT/rel).exists():
                    protected.add(rel)
        for token in argv:
            if token.endswith(".py") and (ROOT/token).exists():
                protected.add(token)
except Exception:
    pass

source_files=[
    rel for rel in files
    if rel.endswith(".py")
    and rel.startswith(SOURCE_PREFIXES)
    and not rel.startswith(NON_RUNTIME_PREFIXES)
]
shell_files=[
    rel for rel in files
    if rel.endswith(".sh")
    and rel.startswith(("scripts/","modules/"))
]

imports={rel:parse_imports(rel) for rel in source_files}

# Build exact duplicate groups excluding package marker noise.
exact_groups=[]
for group in base.get("exact_duplicate_groups") or []:
    members=[f for f in group.get("files",[]) if (ROOT/f).exists()]
    substantive=[
        f for f in members
        if Path(f).name not in {"__init__.py"}
    ]
    if len(substantive)>=2:
        exact_groups.append(substantive)

# Include semantic groups from V68.0.
semantic_groups=[
    [f for f in g.get("files",[]) if (ROOT/f).exists()]
    for g in (base.get("semantic_duplicate_groups") or [])
]
semantic_groups=[g for g in semantic_groups if len(g)>=2]

def structured_refs(target):
    mod=module_name(target)
    src_hits=set()
    test_hits=set()
    shell_hits=set()

    if mod:
        for src,mods in imports.items():
            if src==target:
                continue
            for m in mods:
                if m==mod or m.startswith(mod+"."):
                    src_hits.add(src)

        # package import can also import from parent package __init__.
        parent=mod.rsplit(".",1)[0] if "." in mod else None
        if parent:
            for src,mods in imports.items():
                if src==target:
                    continue
                if parent in mods:
                    # Parent imports are weak evidence; record separately.
                    pass

    # Tests are evidence that a module remains part of the validated surface.
    for rel in files:
        if not rel.endswith(".py"):
            continue
        if not rel.startswith(TEST_PREFIXES):
            continue
        try:
            txt=(ROOT/rel).read_text(errors="ignore")
        except Exception:
            continue
        needles={target}
        if mod:
            needles.add(mod)
        if any(n in txt for n in needles):
            test_hits.add(rel)

    for rel in shell_files:
        if shell_mentions(rel,target):
            shell_hits.add(rel)

    return {
        "source_imports":sorted(src_hits),
        "test_references":sorted(test_hits),
        "shell_entrypoints":sorted(shell_hits),
        "runtime_protected":target in protected,
    }

def role(target):
    p=Path(target)
    if p.name=="plugin.py":
        if target.startswith("marketplace/packages/"):
            return "marketplace_source_package"
        if target.startswith("plugins/installed/"):
            return "installed_plugin_copy"
    if target.startswith("scripts/"):
        return "script_entrypoint"
    if target.startswith("agents/"):
        return "agent_module"
    if target.startswith("companyos/"):
        return "companyos_module"
    if target.startswith("marketplace/"):
        return "marketplace_asset"
    if target.startswith("plugins/"):
        return "plugin_asset"
    return "other"

def classify_group(files, kind):
    ev={f:structured_refs(f) for f in files}
    roles={f:role(f) for f in files}

    protected_members=[f for f in files if ev[f]["runtime_protected"]]
    actively_imported=[
        f for f in files
        if ev[f]["source_imports"] or ev[f]["shell_entrypoints"]
    ]
    test_only=[
        f for f in files
        if not ev[f]["source_imports"]
        and not ev[f]["shell_entrypoints"]
        and ev[f]["test_references"]
    ]
    dormant=[
        f for f in files
        if not ev[f]["runtime_protected"]
        and not ev[f]["source_imports"]
        and not ev[f]["shell_entrypoints"]
        and not ev[f]["test_references"]
    ]

    distinct_roles=len(set(roles.values()))>1

    decision="manual_review"
    keeper=None
    retire=[]

    # Only exact duplicates are eligible for a candidate retirement decision.
    if kind=="exact":
        if distinct_roles:
            decision="keep_role_distinct_copies"
        elif len(protected_members)==1:
            keeper=protected_members[0]
            possible=[f for f in files if f!=keeper and f in dormant]
            if possible:
                decision="candidate_retire_dormant_exact_copies"
                retire=possible
            else:
                decision="keep_no_dormant_exact_copy"
        elif len(actively_imported)==1:
            keeper=actively_imported[0]
            possible=[f for f in files if f!=keeper and f in dormant]
            if possible:
                decision="candidate_retire_dormant_exact_copies"
                retire=possible
            else:
                decision="keep_no_dormant_exact_copy"
        elif len(files)==2 and len(test_only)==1 and len(dormant)==1:
            keeper=test_only[0]
            decision="candidate_retire_dormant_exact_copy"
            retire=dormant
        elif dormant and len(dormant)<len(files):
            decision="manual_review_mixed_active_and_dormant"
        elif len(dormant)==len(files):
            decision="manual_review_all_dormant"
        else:
            decision="keep_or_manual_review_all_active"
    else:
        if distinct_roles:
            decision="keep_role_distinct_semantic_copies"
        else:
            decision="manual_behavior_review_semantic_equivalent"

    return {
        "kind":kind,
        "files":files,
        "sha256":{f:sha256(f) for f in files} if kind=="exact" else {},
        "roles":roles,
        "evidence":ev,
        "protected_members":protected_members,
        "actively_imported_or_entrypoint":actively_imported,
        "test_only":test_only,
        "dormant":dormant,
        "decision":decision,
        "keeper":keeper,
        "retirement_candidates":retire,
    }

records=[]
for g in exact_groups:
    records.append(classify_group(g,"exact"))
for g in semantic_groups:
    records.append(classify_group(g,"semantic"))

retirement_candidates=[]
for rec in records:
    for f in rec["retirement_candidates"]:
        retirement_candidates.append({
            "path":f,
            "keeper":rec["keeper"],
            "kind":rec["kind"],
            "decision":rec["decision"],
            "evidence":rec["evidence"][f],
        })

decision_counts=defaultdict(int)
for r in records:
    decision_counts[r["decision"]]+=1

report={
    "schema":"companyos.v68_1.precise_duplicate_audit.v1",
    "generated_at_unix":time.time(),
    "branch":git("branch","--show-current"),
    "head_sha":git("rev-parse","HEAD"),
    "mode":"AUDIT_ONLY_NO_FILE_MUTATION",
    "tracked_files":len(files),
    "substantive_exact_groups":sum(1 for r in records if r["kind"]=="exact"),
    "semantic_groups":sum(1 for r in records if r["kind"]=="semantic"),
    "decision_counts":dict(sorted(decision_counts.items())),
    "candidate_retirement_count":len(retirement_candidates),
    "candidate_retirements":retirement_candidates,
    "groups":records,
    "deletion_performed":False,
    "move_performed":False,
    "financial_limits_changed":False,
    "next_step":{
        "name":"V68.2 surgical duplicate retirement or canonicalization",
        "rule":"Do not delete by stem/name alone. Only retire exact-content duplicates that have a clear keeper and zero structured runtime/test/entrypoint evidence, with recovery branch and rollback.",
    },
}

OUT_JSON.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")

md=[
    "# CompanyOS V68.1 Precise Duplicate Caller / Role Audit",
    "",
    "This pass uses structured Python imports, shell entrypoints, tests, canonical manifest membership, and supervisor ownership instead of broad text-search counts.",
    "",
    f"- Substantive exact duplicate groups: **{report['substantive_exact_groups']}**",
    f"- Semantic-equivalent groups: **{report['semantic_groups']}**",
    f"- Candidate retirements: **{report['candidate_retirement_count']}**",
    "",
    "## Decisions",
    "",
]
for k,v in sorted(report["decision_counts"].items()):
    md.append(f"- `{k}`: {v}")
md += [
    "",
    "No files were removed in V68.1.",
]
OUT_MD.write_text("\n".join(md)+"\n")

print(json.dumps({
    "status":"PASS",
    "tracked_files":report["tracked_files"],
    "substantive_exact_groups":report["substantive_exact_groups"],
    "semantic_groups":report["semantic_groups"],
    "candidate_retirement_count":report["candidate_retirement_count"],
    "decision_counts":report["decision_counts"],
},indent=2,sort_keys=True))
