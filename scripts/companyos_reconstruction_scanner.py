#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
OUT = ROOT / "docs" / "companyos_reconstruction"
OUT.mkdir(parents=True, exist_ok=True)

EXCLUDE_PARTS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "local_ai", "models", "backups",
}

TEXT_SUFFIXES = {
    ".py", ".sh", ".json", ".md", ".txt", ".yaml", ".yml",
    ".toml", ".ini", ".cfg",
}

PHASE_PATTERNS = [
    re.compile(r"phase[_\- ]?(\d+)", re.I),
    re.compile(r"phases?[_\- ]?(\d+)[_\- ]?(?:to|through|-)[_\- ]?(\d+)", re.I),
    re.compile(r"(\d+)[_\- ]?(?:to|through|-)[_\- ]?(\d+)", re.I),
]

CAPABILITY_KEYWORDS = {
    "autonomous_ceo": ["ceo", "executive", "strategy"],
    "opportunity_engine": ["opportunity", "market", "lead", "venture"],
    "planner": ["planner", "roadmap", "milestone", "task_graph"],
    "builder": ["builder", "codegen", "generator", "self_build"],
    "qa_validation": ["qa", "validation", "verify", "test"],
    "runtime": ["runtime", "supervisor", "watchdog", "worker"],
    "memory": ["memory", "knowledge", "history", "ledger"],
    "finance": ["finance", "treasury", "wallet", "budget"],
    "deployment": ["deploy", "release", "cloudflare", "route"],
    "recovery": ["recovery", "rollback", "repair", "reconcile"],
    "revenue_operations": ["revenue", "sales", "customer", "crm"],
    "portfolio": ["portfolio", "allocation", "scale_candidate"],
    "local_ai": ["llama", "qwen", "local_ai", "openai_compatible"],
    "adaptive_self_build": ["adaptive_self_build", "self_build", "capability_gap"],
}

def save_json(name: str, data: Any) -> None:
    p = OUT / name
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(p)

def iter_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE_PARTS for part in rel.parts):
            continue
        if ".before_" in p.name or ".backup" in p.name:
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if p.stat().st_size > 1_500_000:
            continue
        yield p, rel

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def phase_candidates_for(rel: Path, text: str):
    found = []
    sources = [str(rel), text[:20000]]
    for source in sources:
        for pat in PHASE_PATTERNS:
            for m in pat.finditer(source):
                nums = [int(x) for x in m.groups() if x is not None]
                if not nums:
                    continue
                if len(nums) == 1:
                    found.append((nums[0], nums[0]))
                else:
                    a, b = nums[0], nums[1]
                    if a > b:
                        a, b = b, a
                    if b - a <= 100000:
                        found.append((a, b))
    return found

def python_symbols(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return [], []
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    return funcs, classes

files = []
phase_evidence = defaultdict(list)
capability_hits = defaultdict(list)
symbol_index = defaultdict(list)
hash_groups = defaultdict(list)

for path, rel in iter_files():
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        text = ""

    entry = {
        "path": str(rel),
        "size": path.stat().st_size,
        "modified_at": path.stat().st_mtime,
        "sha256": sha256(path),
    }

    if path.suffix == ".py":
        funcs, classes = python_symbols(path)
        entry["functions"] = funcs[:100]
        entry["classes"] = classes[:100]
        for name in funcs + classes:
            symbol_index[name].append(str(rel))

    files.append(entry)
    hash_groups[entry["sha256"]].append(str(rel))

    for start, end in phase_candidates_for(rel, text):
        if start <= 200000 and end <= 200000:
            phase_evidence[(start, end)].append(str(rel))

    haystack = (str(rel) + "\n" + text[:50000]).lower()
    for capability, keywords in CAPABILITY_KEYWORDS.items():
        score = sum(haystack.count(keyword) for keyword in keywords)
        if score:
            capability_hits[capability].append({
                "path": str(rel),
                "score": score,
            })

phase_ranges = []
for (start, end), evidence in phase_evidence.items():
    phase_ranges.append({
        "start": start,
        "end": end,
        "evidence_count": len(set(evidence)),
        "evidence": sorted(set(evidence))[:50],
    })

phase_ranges.sort(key=lambda x: (x["start"], x["end"]))
highest_phase = max((r["end"] for r in phase_ranges), default=0)

# Estimate confidence from independent evidence.
highest_evidence = [
    r for r in phase_ranges
    if r["end"] == highest_phase
]
confidence = "low"
if highest_evidence:
    total = sum(r["evidence_count"] for r in highest_evidence)
    confidence = "high" if total >= 5 else "medium" if total >= 2 else "low"

capabilities = {}
for capability, hits in capability_hits.items():
    ranked = sorted(hits, key=lambda x: (-x["score"], x["path"]))
    score = sum(x["score"] for x in ranked[:20])
    capabilities[capability] = {
        "status": "present" if score >= 5 else "partial",
        "evidence_score": score,
        "top_evidence": ranked[:15],
    }

duplicates = {
    "identical_file_groups": [
        {"sha256": digest, "files": paths}
        for digest, paths in hash_groups.items()
        if len(paths) > 1
    ],
    "duplicate_symbols": [
        {"symbol": symbol, "files": paths}
        for symbol, paths in symbol_index.items()
        if len(paths) > 1
    ],
}
duplicates["identical_file_groups"].sort(key=lambda x: (-len(x["files"]), x["sha256"]))
duplicates["duplicate_symbols"].sort(key=lambda x: (-len(x["files"]), x["symbol"]))

phase_index = {
    "generated_at": time.time(),
    "repository_root": str(ROOT),
    "files_scanned": len(files),
    "highest_phase_detected": highest_phase,
    "highest_phase_confidence": confidence,
    "phase_ranges": phase_ranges,
}

current_phase = {
    "generated_at": time.time(),
    "highest_phase_detected": highest_phase,
    "confidence": confidence,
    "interpretation": (
        "Highest phase number found in repository evidence. "
        "This does not automatically prove every lower phase completed."
    ),
    "highest_phase_evidence": highest_evidence,
}

save_json("PHASE_INDEX.json", phase_index)
save_json("CURRENT_PHASE.json", current_phase)
save_json("CAPABILITY_MATRIX.json", {
    "generated_at": time.time(),
    "capabilities": capabilities,
})
save_json("DUPLICATE_SYSTEMS_REPORT.json", {
    "generated_at": time.time(),
    "identical_file_group_count": len(duplicates["identical_file_groups"]),
    "duplicate_symbol_count": len(duplicates["duplicate_symbols"]),
    **duplicates,
})

architecture_lines = [
    "# CompanyOS Active Architecture",
    "",
    f"Generated from {len(files)} scanned repository files.",
    "",
    "## Detected capabilities",
    "",
]
for name, info in sorted(capabilities.items()):
    architecture_lines.append(
        f"- **{name}** — {info['status']} "
        f"(evidence score: {info['evidence_score']})"
    )

architecture_lines += [
    "",
    "## Current phase evidence",
    "",
    f"- Highest detected phase: **{highest_phase}**",
    f"- Confidence: **{confidence}**",
    "",
    "## Important limitation",
    "",
    "A phase number appearing in a filename, archive, verifier, or document is evidence, "
    "but not by itself proof that the phase completed successfully. Receipts and verification "
    "results should be used to promote ranges from detected to verified.",
]
(OUT / "ACTIVE_ARCHITECTURE.md").write_text(
    "\n".join(architecture_lines) + "\n",
    encoding="utf-8",
)

history_lines = [
    "# CompanyOS Master History",
    "",
    "This file was generated from repository evidence rather than chat-memory estimates.",
    "",
    "## Canonical current marker",
    "",
    f"- Highest phase detected: **{highest_phase}**",
    f"- Confidence: **{confidence}**",
    "",
    "## Detected phase ranges",
    "",
]
for item in phase_ranges:
    history_lines.append(
        f"- **{item['start']}–{item['end']}** — "
        f"{item['evidence_count']} evidence file(s)"
    )

history_lines += [
    "",
    "## Reconstruction status",
    "",
    "- Phase evidence collected",
    "- Capability inventory generated",
    "- Duplicate files and symbols identified",
    "- Active architecture summary generated",
    "",
    "## Next verification pass",
    "",
    "Cross-reference phase ranges against build receipts, PASS markers, runtime state, "
    "and verification scripts to distinguish detected, built, tested, and operational phases.",
]
(OUT / "COMPANYOS_MASTER_HISTORY.md").write_text(
    "\n".join(history_lines) + "\n",
    encoding="utf-8",
)

print(json.dumps({
    "ok": True,
    "files_scanned": len(files),
    "highest_phase_detected": highest_phase,
    "confidence": confidence,
    "output_directory": str(OUT),
}, indent=2))
