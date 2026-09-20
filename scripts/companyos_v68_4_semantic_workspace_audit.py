#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import ast
import hashlib
import json
import subprocess
import time

ROOT=Path.home()/"companyos"
ROLE_REPORT=ROOT/"audit/COMPANYOS_V68_2_ROLE_RESOLUTION.json"
OUT_JSON=ROOT/"audit/COMPANYOS_V68_4_SEMANTIC_WORKSPACE_AUDIT.json"
OUT_MD=ROOT/"audit/COMPANYOS_V68_4_SEMANTIC_WORKSPACE_AUDIT.md"

UPPER="workspace/Local_Contractor_Bid_Organizer"
LOWER="workspace/local_contractor_bid_organizer"

TEXT_EXT={".py",".sh",".json",".toml",".yaml",".yml",".md",".txt"}

def git(*args):
    return subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()

def file_sha(path: Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def module_name(rel: str):
    if not rel.endswith(".py"):
        return None
    if rel.endswith("/__init__.py"):
        return rel[:-12].replace("/",".")
    return rel[:-3].replace("/",".")

def parse_py(rel: str):
    p=ROOT/rel
    tree=ast.parse(p.read_text(errors="ignore"))
    imports=[]
    exports=[]
    executable=[]
    for node in tree.body:
        if isinstance(node,ast.Import):
            for a in node.names:
                imports.append(a.name)
        elif isinstance(node,ast.ImportFrom):
            imports.append(("."*node.level)+(node.module or ""))
        elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            exports.append(node.name)
        elif isinstance(node,(ast.Assign,ast.AnnAssign)):
            names=[]
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target,ast.Name):
                    names.append(target.id)
            exports.extend(names)
        elif isinstance(node,(ast.Expr,ast.If,ast.For,ast.While,ast.With,ast.Try,ast.Match)):
            executable.append(type(node).__name__)
    sig=hashlib.sha256(
        ast.dump(tree,annotate_fields=True,include_attributes=False).encode()
    ).hexdigest()
    return {
        "ast_sha256":sig,
        "imports":sorted(set(imports)),
        "exports":sorted(set(exports)),
        "top_level_executable_nodes":executable,
    }

tracked=git("ls-files").splitlines()
tracked_set=set(tracked)

source_py=[
    rel for rel in tracked
    if rel.endswith(".py")
    and (
        rel.startswith("companyos/")
        or rel.startswith("scripts/")
        or rel.startswith("agents/")
        or rel.startswith("connectors/")
        or rel.startswith("plugins/")
        or rel.startswith("tests/")
    )
]

parsed_imports={}
for rel in source_py:
    try:
        tree=ast.parse((ROOT/rel).read_text(errors="ignore"))
    except Exception:
        continue
    mods=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module:
            mods.add(node.module)
    parsed_imports[rel]=mods

def structured_refs(target: str):
    mod=module_name(target)
    importers=[]
    test_refs=[]
    path_refs=[]
    if mod:
        for src,mods in parsed_imports.items():
            if src==target:
                continue
            if mod in mods or any(m.startswith(mod+".") for m in mods):
                importers.append(src)
    for src in tracked:
        if src==target:
            continue
        p=ROOT/src
        if not p.is_file() or p.suffix.lower() not in TEXT_EXT:
            continue
        if src.startswith(("audit/","ops/patch_history/","backups/")):
            continue
        try:
            if p.stat().st_size>1_500_000:
                continue
            text=p.read_text(errors="ignore")
        except Exception:
            continue
        if target in text:
            path_refs.append(src)
        if src.startswith("tests/") and mod and mod in text:
            test_refs.append(src)
    return {
        "structured_importers":sorted(set(importers)),
        "test_references":sorted(set(test_refs)),
        "literal_path_references":sorted(set(path_refs)),
    }

role=json.loads(ROLE_REPORT.read_text())
semantic_groups=[
    g for g in (role.get("resolved_groups") or [])
    if g.get("kind")=="semantic"
]

semantic_records=[]
for g in semantic_groups:
    files=[f for f in g.get("files",[]) if f in tracked_set and (ROOT/f).is_file()]
    details={}
    ast_hashes=set()
    byte_hashes=set()
    active_counts={}
    for rel in files:
        info=parse_py(rel)
        refs=structured_refs(rel)
        bsha=file_sha(ROOT/rel)
        details[rel]={
            **info,
            "byte_sha256":bsha,
            "references":refs,
        }
        ast_hashes.add(info["ast_sha256"])
        byte_hashes.add(bsha)
        active_counts[rel]=(
            len(refs["structured_importers"])
            + len(refs["test_references"])
            + len(refs["literal_path_references"])
        )

    if len(ast_hashes)!=1:
        decision="SEMANTIC_EQUIVALENCE_DRIFTED"
        keeper=None
    else:
        active=[f for f,n in active_counts.items() if n>0]
        if len(active)>1:
            decision="KEEP_ROLE_ISOLATED_EQUIVALENTS"
            keeper=None
        elif len(active)==1:
            decision="SINGLE_ACTIVE_CANONICALIZATION_CANDIDATE"
            keeper=active[0]
        else:
            decision="ALL_DORMANT_REQUIRES_SUBSYSTEM_OWNER_DECISION"
            keeper=None

    semantic_records.append({
        "files":files,
        "ast_equivalent":len(ast_hashes)==1,
        "byte_identical":len(byte_hashes)==1,
        "active_reference_counts":active_counts,
        "decision":decision,
        "provisional_keeper":keeper,
        "details":details,
    })

def workspace_tree(relroot: str):
    base=ROOT/relroot
    rows={}
    if not base.exists():
        return rows
    for p in sorted(x for x in base.rglob("*") if x.is_file()):
        rel=p.relative_to(base).as_posix()
        if rel.startswith("companyos_progress/") or "/companyos_progress/" in rel:
            continue
        rows[rel]={
            "bytes":p.stat().st_size,
            "sha256":file_sha(p),
        }
    return rows

upper=workspace_tree(UPPER)
lower=workspace_tree(LOWER)

upper_keys=set(upper)
lower_keys=set(lower)
common=upper_keys & lower_keys
same=sorted(k for k in common if upper[k]["sha256"]==lower[k]["sha256"])
different=sorted(k for k in common if upper[k]["sha256"]!=lower[k]["sha256"])
upper_only=sorted(upper_keys-lower_keys)
lower_only=sorted(lower_keys-upper_keys)

workspace_refs={UPPER:[],LOWER:[]}
for rel in tracked:
    if rel.startswith(UPPER+"/") or rel.startswith(LOWER+"/"):
        continue
    p=ROOT/rel
    if not p.is_file() or p.suffix.lower() not in TEXT_EXT:
        continue
    if rel.startswith(("audit/","ops/patch_history/","backups/")):
        continue
    try:
        if p.stat().st_size>1_500_000:
            continue
        txt=p.read_text(errors="ignore")
    except Exception:
        continue
    for target in (UPPER,LOWER):
        if target in txt:
            workspace_refs[target].append(rel)

workspace_refs={k:sorted(set(v)) for k,v in workspace_refs.items()}

if not different and not upper_only and not lower_only:
    workspace_decision="TREES_EQUIVALENT_CANONICAL_PATH_SELECTION_ONLY"
elif workspace_refs[UPPER] and not workspace_refs[LOWER]:
    workspace_decision="UPPER_REFERENCED_BUT_CONTENT_MERGE_REQUIRED"
elif workspace_refs[LOWER] and not workspace_refs[UPPER]:
    workspace_decision="LOWER_REFERENCED_BUT_CONTENT_MERGE_REQUIRED"
elif workspace_refs[UPPER] and workspace_refs[LOWER]:
    workspace_decision="BOTH_REFERENCED_MANUAL_MERGE_REQUIRED"
else:
    workspace_decision="UNREFERENCED_DIVERGENT_WORKSPACES_MANUAL_MERGE_REQUIRED"

workspace={
    "upper_path":UPPER,
    "lower_path":LOWER,
    "upper_file_count":len(upper),
    "lower_file_count":len(lower),
    "same_relative_files":same,
    "same_relative_file_count":len(same),
    "different_relative_files":different,
    "different_relative_file_count":len(different),
    "upper_only_files":upper_only,
    "lower_only_files":lower_only,
    "references":workspace_refs,
    "decision":workspace_decision,
}

report={
    "schema":"companyos.v68_4.semantic_workspace_audit.v1",
    "generated_at_unix":time.time(),
    "branch":git("branch","--show-current"),
    "head_sha":git("rev-parse","HEAD"),
    "mode":"AUDIT_ONLY_NO_FILE_MUTATION",
    "semantic_group_count":len(semantic_records),
    "semantic_groups":semantic_records,
    "workspace_identity_audit":workspace,
    "deletion_performed":False,
    "move_performed":False,
    "financial_limits_changed":False,
    "next_step":{
        "name":"V68.5 targeted canonicalization",
        "rule":"Only canonicalize a semantic group if one implementation has clear structured ownership and the others have no independent callers/tests. Workspace trees require file-level merge planning before either path can be retired.",
    },
}
OUT_JSON.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")

lines=[
    "# CompanyOS V68.4 Semantic + Workspace Identity Audit",
    "",
    "No files were moved or deleted.",
    "",
    f"- Semantic-equivalent groups reviewed: **{len(semantic_records)}**",
    f"- Workspace upper files: **{len(upper)}**",
    f"- Workspace lower files: **{len(lower)}**",
    f"- Same relative files: **{len(same)}**",
    f"- Different relative files: **{len(different)}**",
    f"- Upper-only files: **{len(upper_only)}**",
    f"- Lower-only files: **{len(lower_only)}**",
    f"- Workspace decision: **{workspace_decision}**",
    "",
    "## Semantic decisions",
]
for idx,g in enumerate(semantic_records,1):
    lines.append(f"- Group {idx}: `{g['decision']}`")
OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")

print(json.dumps({
    "status":"PASS",
    "semantic_group_count":len(semantic_records),
    "semantic_decisions":[g["decision"] for g in semantic_records],
    "workspace_decision":workspace_decision,
    "workspace_same_files":len(same),
    "workspace_different_files":len(different),
    "workspace_upper_only":len(upper_only),
    "workspace_lower_only":len(lower_only),
    "workspace_upper_refs":len(workspace_refs[UPPER]),
    "workspace_lower_refs":len(workspace_refs[LOWER]),
},indent=2,sort_keys=True))
