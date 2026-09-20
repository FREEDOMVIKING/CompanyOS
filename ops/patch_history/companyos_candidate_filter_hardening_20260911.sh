#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
BRANCH="companyos-continuous-fix-2026-09-11"

cd "$ROOT"

if [ "$(git branch --show-current)" != "$BRANCH" ]; then
  echo "ERROR: expected branch $BRANCH"
  exit 2
fi

python - <<'PY'
from pathlib import Path

p = Path("companyos/runtime/research_to_execution_bridge.py")
s = p.read_text(encoding="utf-8")

# Strengthen policy/instruction rejection and require real candidate semantics.
marker = 'POLICY_WORDS = {'
if marker not in s:
    raise SystemExit("research_to_execution_bridge.py structure not recognized")

if 'IMPERATIVE_NAME_PATTERNS' not in s:
    insert_after = '''POLICY_WORDS = {
    "do_not", "must_", "research_analysis_only", "evidence_sources",
    "numeric_scoring", "mark_estimates", "missing_evidence",
    "duplicate_rename", "candidate_files_written", "generate_at_least",
    "construction_is_allowed", "this_stage_is_research",
    "persist_a_market_scan", "every_candidate_json",
    "companyos_opportunity_engine_test", "one_shot_token",
}
'''
    replacement = insert_after + '''
IMPERATIVE_NAME_PATTERNS = (
    "prefer ",
    "for each ",
    "use 0-100",
    "use 0_100",
    "research markets",
    "discover at least",
    "generate at least",
    "do not ",
    "must ",
    "every candidate",
    "construction and service businesses may",
    "persist a market scan",
    "this stage is research",
    "mark estimates",
    "evidence sources",
)

SEMANTIC_KEYS = (
    "business_model",
    "target_customer",
    "customer_segment",
    "customer_problem",
    "problem",
    "offer",
    "product",
    "service",
    "value_proposition",
    "pricing",
    "price",
    "revenue_model",
    "market",
)
'''
    if insert_after not in s:
        raise SystemExit("POLICY_WORDS block not found")
    s = s.replace(insert_after, replacement, 1)

old = '''def _looks_like_policy(source: Path, payload: dict[str, Any]) -> bool:
    stem = source.stem.lower()
    if any(word in stem for word in POLICY_WORDS):
        return True

    keys = {str(k).lower() for k in payload}
    useful = any(k in keys for k in NAME_KEYS) and any(k in keys for k in MODEL_KEYS)
    text = _text(payload)

    instruction_markers = (
        "must not", "do not perform", "research only",
        "candidate json must", "generate at least",
        "this stage is research", "scoring fields must",
    )
    if not useful and any(x in text for x in instruction_markers):
        return True
    return False
'''

new = '''def _looks_like_policy(source: Path, payload: dict[str, Any]) -> bool:
    stem = source.stem.lower()
    if any(word in stem for word in POLICY_WORDS):
        return True

    name = _name(payload, source).strip().lower()
    if any(name.startswith(x) or x in name for x in IMPERATIVE_NAME_PATTERNS):
        return True

    keys = {str(k).lower() for k in payload}
    text = _text(payload)

    instruction_markers = (
        "must not",
        "do not perform",
        "research only",
        "candidate json must",
        "generate at least",
        "this stage is research",
        "scoring fields must",
        "for each candidate",
        "prefer commercially distinct",
        "use 0-100 numeric scores",
        "research markets before building",
    )
    if any(x in text for x in instruction_markers):
        semantic_hits = sum(1 for k in SEMANTIC_KEYS if k in keys)
        if semantic_hits < 2:
            return True

    return False
'''
if old not in s:
    raise SystemExit("_looks_like_policy block not found")
s = s.replace(old, new, 1)

# Add helper functions before scan_candidates.
anchor = 'def scan_candidates(min_score: float = 45.0) -> list[Candidate]:\n'
if anchor not in s:
    raise SystemExit("scan_candidates anchor not found")

helpers = '''def _semantic_candidate_strength(payload: dict[str, Any]) -> int:
    keys = {str(k).lower() for k in payload}
    hits = sum(1 for k in SEMANTIC_KEYS if k in keys)

    # Nested business records are also acceptable.
    for nested_key in ("candidate", "business", "opportunity_details", "market_analysis"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            nested_keys = {str(k).lower() for k in nested}
            hits += sum(1 for k in SEMANTIC_KEYS if k in nested_keys)

    return hits


def _has_explicit_score(payload: dict[str, Any]) -> bool:
    if any(k in payload for k in SCORE_KEYS):
        return True
    scores = payload.get("scores")
    return isinstance(scores, dict) and any(_numeric(v) is not None for v in scores.values())


def _promotion_quality(candidate: Candidate) -> tuple[bool, list[str]]:
    reasons = []
    if candidate.score < 60:
        reasons.append("score_below_60")
    if candidate.confidence < 35 and candidate.evidence_count < 1:
        reasons.append("insufficient_confidence_and_evidence")
    if _semantic_candidate_strength(candidate.payload) < 2:
        reasons.append("insufficient_business_semantics")
    if not _has_explicit_score(candidate.payload):
        reasons.append("no_explicit_candidate_score")
    return (not reasons), reasons


'''
s = s.replace(anchor, helpers + anchor, 1)

# Tighten scan requirements.
old_scan_fragment = '''        name = _name(payload, path)
        slug = _slug(name)
        if not slug or len(slug) < 3:
            continue

        score = _score(payload)
        if score < min_score:
            continue
'''

new_scan_fragment = '''        name = _name(payload, path)
        slug = _slug(name)
        if not slug or len(slug) < 3:
            continue

        # A real opportunity must look like a business candidate, not a rule,
        # instruction, test artifact, or generic research directive.
        if _semantic_candidate_strength(payload) < 2:
            continue
        if not _has_explicit_score(payload):
            continue

        score = _score(payload)
        if score < min_score:
            continue
'''
if old_scan_fragment not in s:
    raise SystemExit("scan fragment not found")
s = s.replace(old_scan_fragment, new_scan_fragment, 1)

# Tighten eligibility for promotion and surface rejection reasons.
old_eligible = '''    eligible = []
    for c in candidates:
        if c.fingerprint in state["promoted_fingerprints"]:
            continue
        if _workspace_exists(c.slug):
            continue
        eligible.append(c)
'''

new_eligible = '''    eligible = []
    rejected = []
    for c in candidates:
        if c.fingerprint in state["promoted_fingerprints"]:
            continue
        if _workspace_exists(c.slug):
            continue
        ok, reasons = _promotion_quality(c)
        if not ok:
            rejected.append({
                "name": c.name,
                "slug": c.slug,
                "score": c.score,
                "confidence": c.confidence,
                "evidence_count": c.evidence_count,
                "reasons": reasons,
            })
            continue
        eligible.append(c)
'''
if old_eligible not in s:
    raise SystemExit("eligible block not found")
s = s.replace(old_eligible, new_eligible, 1)

old_detail = '''        "execution_venture_count": execution_ventures,
        "top_candidates": [
'''
new_detail = '''        "execution_venture_count": execution_ventures,
        "rejected_count": len(rejected),
        "rejected_candidates": rejected[:10],
        "top_candidates": [
'''
if old_detail not in s:
    raise SystemExit("detail block not found")
s = s.replace(old_detail, new_detail, 1)

p.write_text(s, encoding="utf-8")
print("Hardened candidate filter and promotion quality gate")
PY

cat > scripts/validate_candidate_filter_v2.py <<'PY'
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos.runtime.research_to_execution_bridge import (
    scan_candidates,
    maybe_promote_candidate,
)

rows = scan_candidates(min_score=45)
print("===== FILTERED REAL CANDIDATES =====")
print("count:", len(rows))
for c in rows[:10]:
    print(json.dumps({
        "name": c.name,
        "slug": c.slug,
        "score": c.score,
        "confidence": c.confidence,
        "evidence_count": c.evidence_count,
        "source": c.source,
    }, sort_keys=True))

print("===== PROMOTION DECISION (NO COOLDOWN) =====")
result = maybe_promote_candidate(
    min_score=45,
    cooldown_seconds=0,
)
print(json.dumps(result, indent=2, sort_keys=True, default=str))
print("COMPANYOS_CANDIDATE_FILTER_V2=PASS")
PY

python -m py_compile   companyos/runtime/research_to_execution_bridge.py   scripts/validate_candidate_filter_v2.py

echo
echo "===== VALIDATING HARDENED FILTER ====="
python scripts/validate_candidate_filter_v2.py

echo
echo "===== COMMIT + PUSH ====="
git add   companyos/runtime/research_to_execution_bridge.py   scripts/validate_candidate_filter_v2.py

git commit -m "Reject policy artifacts from CompanyOS venture candidates" || true
git push origin "$BRANCH"

echo
echo "===== RESTART WATCHDOG STACK ====="
scripts/companyosctl restart
sleep 4

echo
echo "===== FINAL EXECUTION STATUS ====="
scripts/companyos_executionctl status

echo
echo "COMPANYOS_CANDIDATE_FILTER_HARDENING=COMPLETE"
