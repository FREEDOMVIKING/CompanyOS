#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RECON = ROOT / "docs" / "companyos_reconstruction"
RECON.mkdir(parents=True, exist_ok=True)

PHASE_RE = re.compile(r"phase[_\- ]?(\d+)", re.I)

EXCLUDE_PARTS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "local_ai", "models",
}

LOW_TRUST_PATH_TOKENS = {
    "research_output",
    "canonical_research_outputs",
    "generated",
    "staging",
    "rejected",
    "backup",
    "backups",
    "archive",
    "archives",
    "tmp",
    "temp",
}

HIGH_TRUST_PATH_TOKENS = {
    "receipt",
    "receipts",
    "verify",
    "verifier",
    "manifest",
    "release",
    "deployment",
    "runtime",
    "state",
    "ledger",
}

PASS_MARKERS = (
    "pass",
    '"ok": true',
    "'ok': true",
    '"success": true',
    "'success': true",
    '"completed": true',
    "'completed': true",
    '"rolled_back": false',
    "'rolled_back': false",
)

FAIL_MARKERS = (
    "fail",
    '"ok": false',
    "'ok': false",
    '"success": false',
    "'success': false",
    '"rolled_back": true',
    "'rolled_back': true",
    "traceback",
    "syntaxerror",
    "exception",
)

def safe_read(path: Path, limit: int = 500_000) -> str:
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def extract_phases(text: str):
    return [int(m.group(1)) for m in PHASE_RE.finditer(text)]

def path_tokens(path: Path):
    return {part.lower() for part in path.parts}

def classify_evidence(path: Path, text: str, phase: int) -> dict[str, Any]:
    rel = path.relative_to(ROOT)
    rel_s = str(rel)
    lower_path = rel_s.lower()
    lower_text = text.lower()
    tokens = path_tokens(rel)

    score = 0
    reasons = []
    blockers = []

    # Base path authority.
    if any(tok in lower_path for tok in HIGH_TRUST_PATH_TOKENS):
        score += 25
        reasons.append("high_trust_path")

    if any(tok in lower_path for tok in LOW_TRUST_PATH_TOKENS):
        score -= 35
        reasons.append("low_trust_generated_or_archive_path")

    if rel.suffix.lower() == ".json":
        score += 8
        reasons.append("structured_json_evidence")

    if rel.suffix.lower() in {".sh", ".py"} and ("verify" in lower_path or "test" in lower_path):
        score += 12
        reasons.append("verification_artifact")

    # Completion and failure markers.
    pass_hits = sum(marker in lower_text for marker in PASS_MARKERS)
    fail_hits = sum(marker in lower_text for marker in FAIL_MARKERS)

    if pass_hits:
        score += min(pass_hits * 12, 48)
        reasons.append(f"pass_markers:{pass_hits}")

    if fail_hits:
        score -= min(fail_hits * 15, 60)
        blockers.append(f"failure_markers:{fail_hits}")

    # Strong receipt semantics.
    if '"ok": true' in lower_text and '"rolled_back": false' in lower_text:
        score += 35
        reasons.append("successful_non_rollback_receipt")

    if '"ok": false' in lower_text or '"rolled_back": true' in lower_text:
        score -= 40
        blockers.append("failed_or_rolled_back_receipt")

    # Match phase specifically in nearby text where practical.
    exact_token = f"phase{phase}"
    if exact_token in lower_text or exact_token in lower_path:
        score += 5
        reasons.append("exact_phase_reference")

    # Penalize absurd isolated high values unless independently verified.
    if phase > 50000 and score < 50:
        score -= 30
        blockers.append("very_high_phase_without_strong_verification")

    status = "unverified"
    if score >= 70 and not blockers:
        status = "verified"
    elif score >= 45:
        status = "probable"
    elif score >= 20:
        status = "detected"

    return {
        "phase": phase,
        "path": rel_s,
        "score": score,
        "status": status,
        "reasons": reasons,
        "blockers": blockers,
    }

evidence_by_phase = defaultdict(list)

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_PARTS for part in rel.parts):
        continue

    if ".before_" in path.name:
        continue

    # Parse phase references from both path and small text files.
    path_phases = extract_phases(str(rel))
    text = safe_read(path)
    text_phases = extract_phases(text[:100_000]) if text else []

    for phase in sorted(set(path_phases + text_phases)):
        if phase <= 0 or phase > 200000:
            continue
        evidence_by_phase[phase].append(classify_evidence(path, text, phase))

phase_rows = []
for phase, items in evidence_by_phase.items():
    items = sorted(items, key=lambda x: (-x["score"], x["path"]))
    strong = [x for x in items if x["status"] == "verified"]
    probable = [x for x in items if x["status"] == "probable"]

    aggregate = sum(max(x["score"], 0) for x in items[:10])
    independent_paths = len({x["path"] for x in items})

    if len(strong) >= 1 and independent_paths >= 1:
        authority = "verified"
    elif len(probable) >= 2 or aggregate >= 100:
        authority = "probable"
    elif aggregate >= 30:
        authority = "detected"
    else:
        authority = "weak"

    phase_rows.append({
        "phase": phase,
        "authority": authority,
        "aggregate_score": aggregate,
        "evidence_count": len(items),
        "independent_paths": independent_paths,
        "top_evidence": items[:20],
    })

phase_rows.sort(key=lambda x: x["phase"])

verified = [x for x in phase_rows if x["authority"] == "verified"]
probable = [x for x in phase_rows if x["authority"] == "probable"]

highest_verified = max((x["phase"] for x in verified), default=0)
highest_probable = max((x["phase"] for x in probable), default=0)
highest_detected = max((x["phase"] for x in phase_rows), default=0)

canonical_phase = highest_verified or highest_probable or highest_detected
canonical_basis = (
    "verified" if highest_verified
    else "probable" if highest_probable
    else "detected"
)

report = {
    "generated_at": time.time(),
    "repository_root": str(ROOT),
    "highest_verified_phase": highest_verified,
    "highest_probable_phase": highest_probable,
    "highest_detected_phase": highest_detected,
    "canonical_current_phase": canonical_phase,
    "canonical_basis": canonical_basis,
    "phase_count_with_evidence": len(phase_rows),
    "important_note": (
        "Canonical phase is selected from weighted repository evidence. "
        "Generated research filenames and isolated large numbers are penalized."
    ),
    "phases": phase_rows,
}

out = RECON / "PHASE_AUTHORITY_REPORT.json"
tmp = out.with_suffix(".json.tmp")
tmp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
tmp.replace(out)

summary = [
    "# CompanyOS Verified Current Phase",
    "",
    f"- **Canonical current phase:** {canonical_phase}",
    f"- **Authority basis:** {canonical_basis}",
    f"- **Highest verified phase:** {highest_verified}",
    f"- **Highest probable phase:** {highest_probable}",
    f"- **Highest detected phase:** {highest_detected}",
    "",
    "## Interpretation",
    "",
    "This report discounts generated research outputs, archives, backups, temporary files, "
    "and isolated oversized phase numbers unless they are supported by successful receipts, "
    "PASS markers, verifiers, manifests, runtime state, or deployment evidence.",
    "",
]

selected = next((x for x in phase_rows if x["phase"] == canonical_phase), None)
if selected:
    summary += [
        "## Canonical phase evidence",
        "",
        f"- Aggregate score: {selected['aggregate_score']}",
        f"- Evidence count: {selected['evidence_count']}",
        f"- Independent paths: {selected['independent_paths']}",
        "",
    ]
    for item in selected["top_evidence"][:10]:
        summary.append(
            f"- `{item['path']}` — score {item['score']} — {item['status']}"
        )

summary_path = RECON / "VERIFIED_CURRENT_PHASE.md"
summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "canonical_current_phase": canonical_phase,
    "canonical_basis": canonical_basis,
    "highest_verified_phase": highest_verified,
    "highest_probable_phase": highest_probable,
    "highest_detected_phase": highest_detected,
    "report": str(out),
    "summary": str(summary_path),
}, indent=2))
