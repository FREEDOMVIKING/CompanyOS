#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

from collections import defaultdict, Counter
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import time

ROOT=Path.home()/"companyos"
MANIFEST=ROOT/"config/companyos_active_component_manifest.json"
OUT_JSON=ROOT/"audit/COMPANYOS_V68_DUPLICATE_CURRENT_AUDIT.json"
OUT_MD=ROOT/"audit/COMPANYOS_V68_DUPLICATE_CURRENT_AUDIT.md"

TEXT_EXT={".py",".sh",".json",".toml",".yaml",".yml",".md",".txt"}
CODE_EXT={".py",".sh"}


def git(*args: str) -> str:
    cp=subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True,check=True)
    return cp.stdout.strip()


def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def python_ast_hash(p: Path) -> str | None:
    try:
        tree=ast.parse(p.read_text(errors="ignore"))
        dump=ast.dump(tree,annotate_fields=True,include_attributes=False)
        return hashlib.sha256(dump.encode()).hexdigest()
    except Exception:
        return None


def is_historical(rel: str) -> bool:
    low=rel.lower()
    first=rel.split("/",1)[0]
    return (
        rel.startswith(("backups/","ops/patch_history/"))
        or first.startswith("companyos_phase")
        or bool(re.match(r"(?i)^phase\d",first))
        or "_bundle" in first.lower()
        or "_backup_" in low
        or ".backup_" in low
        or low.endswith((".zip",".backup",".bak",".bak2"))
    )


def load_protected() -> set[str]:
    protected=set()
    d=json.loads(MANIFEST.read_text())
    for rec in (d.get("component_status") or {}).values():
        if isinstance(rec,dict) and rec.get("path"):
            protected.add(rec["path"])

    # Supervisor-managed modules are protected even if the manifest omitted one.
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

    protected.update({
        "scripts/companyosctl",
        "scripts/companyos_launchctl",
        "scripts/companyos_qualify",
        "scripts/validate_companyos_full_launch.py",
        "scripts/companyos_full_sync_audit.sh",
        "scripts/companyos_consolidation_audit.py",
        "scripts/companyos_duplicate_current_audit.py",
        "config/companyos_active_component_manifest.json",
    })
    return protected


tracked=git("ls-files").splitlines()
protected=load_protected()

# Current duplicate analysis deliberately excludes audit/config/test reports from
# candidate retirement. They can share names by design and are validation data.
candidate_files=[]
for rel in tracked:
    p=ROOT/rel
    if not p.is_file():
        continue
    if rel.startswith(("audit/","config/","tests/")):
        continue
    if is_historical(rel):
        continue
    if p.suffix.lower() not in CODE_EXT:
        continue
    candidate_files.append(rel)

# Active source surface used for caller/reference evidence.
reference_surface=[]
for rel in tracked:
    p=ROOT/rel
    if not p.is_file():
        continue
    if is_historical(rel):
        continue
    if rel.startswith("audit/"):
        continue
    if p.suffix.lower() not in TEXT_EXT:
        continue
    try:
        if p.stat().st_size <= 1_500_000:
            reference_surface.append(rel)
    except Exception:
        pass

# Basename/stem groups.
stem_groups=defaultdict(list)
basename_groups=defaultdict(list)
for rel in candidate_files:
    p=Path(rel)
    stem_groups[p.stem].append(rel)
    basename_groups[p.name].append(rel)

duplicate_stems={k:sorted(v) for k,v in stem_groups.items() if len(v)>1}
duplicate_basenames={k:sorted(v) for k,v in basename_groups.items() if len(v)>1}

# Exact byte duplicates.
sha_groups=defaultdict(list)
for rel in candidate_files:
    p=ROOT/rel
    try:
        sha_groups[sha256_file(p)].append(rel)
    except Exception:
        pass
exact_groups=[sorted(v) for v in sha_groups.values() if len(v)>1]
exact_groups.sort(key=lambda g:(-len(g),g[0]))

# Python AST-equivalent groups catch formatting/comment-only drift.
ast_groups=defaultdict(list)
for rel in candidate_files:
    if not rel.endswith(".py"):
        continue
    sig=python_ast_hash(ROOT/rel)
    if sig:
        ast_groups[sig].append(rel)
semantic_groups=[]
for sig,files in ast_groups.items():
    if len(files)>1:
        unique_byte_hashes={sha256_file(ROOT/f) for f in files}
        if len(unique_byte_hashes)>1:
            semantic_groups.append(sorted(files))
semantic_groups.sort(key=lambda g:(-len(g),g[0]))

# Import evidence for Python modules.
imports_by_file=defaultdict(set)
for rel in reference_surface:
    if not rel.endswith(".py"):
        continue
    p=ROOT/rel
    try:
        tree=ast.parse(p.read_text(errors="ignore"))
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            for alias in node.names:
                imports_by_file[rel].add(alias.name)
        elif isinstance(node,ast.ImportFrom) and node.module:
            imports_by_file[rel].add(node.module)

def module_name(rel: str) -> str | None:
    if not rel.endswith(".py"):
        return None
    return rel[:-3].replace("/",".")

def active_ref_count(target: str) -> tuple[int,list[str]]:
    hits=set()
    mod=module_name(target)
    base=Path(target).name
    stem=Path(target).stem

    # Structured import evidence first.
    if mod:
        for src,mods in imports_by_file.items():
            if src==target:
                continue
            for imported in mods:
                if imported==mod or imported.startswith(mod+"."):
                    hits.add(src)

    # Then bounded literal-path/basename evidence.
    needles={target}
    if base not in {"__init__.py","cli.py","status.py","audit.py"}:
        needles.add(base)
    if stem not in {"__init__","cli","status","audit","test","verify"} and len(stem)>=8:
        needles.add(stem)

    for src in reference_surface:
        if src==target or src in hits:
            continue
        p=ROOT/src
        try:
            text=p.read_text(errors="ignore")
        except Exception:
            continue
        if any(n in text for n in needles):
            hits.add(src)

    return len(hits),sorted(hits)[:30]

# Build evidence once for every member of a duplicate stem or exact group.
interesting=set()
for files in duplicate_stems.values():
    interesting.update(files)
for group in exact_groups:
    interesting.update(group)
for group in semantic_groups:
    interesting.update(group)

refs={}
for rel in sorted(interesting):
    n,h=active_ref_count(rel)
    refs[rel]={"count":n,"examples":h}

def choose_keeper(files: list[str]) -> tuple[str|None,str]:
    protected_hits=[f for f in files if f in protected]
    if len(protected_hits)==1:
        return protected_hits[0],"single_protected_canonical"
    if len(protected_hits)>1:
        return None,"multiple_protected_candidates"

    # If exactly one file has active references and the others do not, treat the
    # referenced implementation as the likely keeper. Still audit-only.
    referenced=[f for f in files if refs.get(f,{}).get("count",0)>0]
    if len(referenced)==1:
        return referenced[0],"single_referenced_candidate"

    return None,"manual_review_required"

# Exact duplicate retirement candidates: same bytes, one clear keeper, and
# unprotected duplicates with zero active references.
exact_records=[]
safe_exact_retire=[]
for files in exact_groups:
    keeper,reason=choose_keeper(files)
    retire=[]
    if keeper:
        for f in files:
            if f==keeper or f in protected:
                continue
            if refs.get(f,{}).get("count",0)==0:
                retire.append(f)
                safe_exact_retire.append({
                    "path":f,
                    "keeper":keeper,
                    "evidence":"exact_sha256_duplicate_and_zero_active_refs",
                })
    exact_records.append({
        "files":files,
        "keeper":keeper,
        "keeper_reason":reason,
        "retirement_candidates":retire,
        "references":{f:refs.get(f,{"count":0,"examples":[]}) for f in files},
    })

# Semantic-equivalent candidates are never auto-retire recommendations yet;
# they need behavior/import review because module-level side effects may differ.
semantic_records=[]
for files in semantic_groups:
    keeper,reason=choose_keeper(files)
    semantic_records.append({
        "files":files,
        "keeper":keeper,
        "keeper_reason":reason,
        "references":{f:refs.get(f,{"count":0,"examples":[]}) for f in files},
        "recommended_action":"manual_behavior_review",
    })

# Stem shadows: same implementation name in multiple current places.
shadow_records=[]
for stem,files in sorted(duplicate_stems.items()):
    if stem in {"__init__","cli","status","audit","verify","install","test"}:
        continue
    keeper,reason=choose_keeper(files)
    unreferenced=[
        f for f in files
        if f!=keeper and f not in protected and refs.get(f,{}).get("count",0)==0
    ]
    shadow_records.append({
        "stem":stem,
        "files":files,
        "keeper":keeper,
        "keeper_reason":reason,
        "unreferenced_noncanonical":unreferenced,
        "references":{f:refs.get(f,{"count":0,"examples":[]}) for f in files},
    })

report={
    "schema":"companyos.v68.duplicate_current_audit.v1",
    "generated_at_unix":time.time(),
    "branch":git("branch","--show-current"),
    "head_sha":git("rev-parse","HEAD"),
    "mode":"AUDIT_ONLY_NO_FILE_MUTATION",
    "tracked_files":len(tracked),
    "candidate_code_files":len(candidate_files),
    "protected_paths":len(protected),
    "duplicate_stem_groups":len(duplicate_stems),
    "duplicate_basename_groups":len(duplicate_basenames),
    "exact_content_duplicate_groups":len(exact_groups),
    "semantic_python_duplicate_groups":len(semantic_groups),
    "safe_exact_retirement_candidates":safe_exact_retire,
    "safe_exact_retirement_candidate_count":len(safe_exact_retire),
    "exact_duplicate_groups":exact_records,
    "semantic_duplicate_groups":semantic_records,
    "duplicate_stem_shadows":shadow_records,
    "deletion_performed":False,
    "move_performed":False,
    "financial_limits_changed":False,
    "next_step":{
        "name":"V68.1 exact duplicate retirement",
        "scope":"only safe_exact_retirement_candidates",
        "requires":[
            "remote recovery branch",
            "exact SHA256 match",
            "one clear keeper",
            "zero active references to retired copy",
            "full pytest",
            "runtime health",
            "launch readiness",
            "automatic rollback on failure"
        ],
    },
}

OUT_JSON.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")

lines=[
    "# CompanyOS V68.0 Duplicate-Current Implementation Audit",
    "",
    "No files were moved or deleted.",
    "",
    f"- Tracked files: **{report['tracked_files']}**",
    f"- Candidate current code files: **{report['candidate_code_files']}**",
    f"- Protected paths: **{report['protected_paths']}**",
    f"- Duplicate stem groups: **{report['duplicate_stem_groups']}**",
    f"- Exact-content duplicate groups: **{report['exact_content_duplicate_groups']}**",
    f"- Python AST-equivalent groups: **{report['semantic_python_duplicate_groups']}**",
    f"- Safe exact-retirement candidates: **{report['safe_exact_retirement_candidate_count']}**",
    "",
    "## Rule for V68.1",
    "",
    "Only exact-byte duplicates with one clear keeper and zero active references to the duplicate copy may be considered for the first retirement batch.",
]
OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")

print(json.dumps({
    "status":"PASS",
    "tracked_files":report["tracked_files"],
    "candidate_code_files":report["candidate_code_files"],
    "protected_paths":report["protected_paths"],
    "duplicate_stem_groups":report["duplicate_stem_groups"],
    "duplicate_basename_groups":report["duplicate_basename_groups"],
    "exact_content_duplicate_groups":report["exact_content_duplicate_groups"],
    "semantic_python_duplicate_groups":report["semantic_python_duplicate_groups"],
    "safe_exact_retirement_candidates":report["safe_exact_retirement_candidate_count"],
},indent=2,sort_keys=True))
